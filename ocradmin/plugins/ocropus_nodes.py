"""
Ocropus OCR processing nodes.
"""

import os
import sys

import plugins
import node
import manager
import stages
#reload(node)

import ocrolib

class UnknownOcropusNodeType(StandardError):
    pass


def makesafe(val):
    if isinstance(val, unicode):
        return val.encode()
    return val


class OcropusFileInNode(node.Node):
    """
    A node that takes a file and returns a numpy object.
    """
    name = "Ocropus::FileIn"
    description = "File Input Node"
    arity = 0
    stage = stages.INPUT
    _parameters = [dict(name="path", value="")]
        

    def validate(self):
        super(OcropusFileInNode, self).validate()
        if not self._params.get("path"):
            raise node.UnsetParameterError("path")

    def _eval(self):
        ba = ocrolib.iulib.bytearray()
        ocrolib.iulib.read_image_binary(
                ba, makesafe(self._params.get("path")))
        return ocrolib.narray2numpy(ba)
        
    

class OcropusBase(node.Node):
    """
    Wrapper around Ocropus component interface.
    """
    _comp = None
    name = "base"

    def __init__(self, **kwargs):
        """
        Initialise with the ocropus component.  
        """
        super(OcropusBase, self).__init__(**kwargs)

    def _set_p(self, p, v):
        """
        Set a component param.
        """
        self._comp.pset(makesafe(p), makesafe(v))

    @classmethod
    def parameters(cls):
        """
        Get parameters from an Ocropus Node.
        """
        p = []
        for i in range(cls._comp.plength()):
            n = cls._comp.pname(i)
            p.append(dict(
                name=n,
                value=cls._comp.pget(n),
            ))
        return p            


class OcropusBinarizeBase(OcropusBase):
    """
    Binarize an image with an Ocropus component.
    """
    arity = 1
    stage = stages.BINARIZE

    def _eval(self):
        """
        Perform binarization on an image.
        
        input: a grayscale image.
        return: a binary image.
        """
        input = self.eval_input(0)
        return self._comp.binarize(input)[0]


class OcropusSegmentPageBase(OcropusBase):
    """
    Segment an image using Ocropus.
    """
    arity = 1
    stage = stages.PAGE_SEGMENT

    def _eval(self):
        """
        Segment a binary image.

        input: a binary image.
        return: a dictionary of box types:
            lines
            paragraphs
            columns
            images
        """
        input = self.eval_input(0)
        page_seg = self._comp.segment(input)
        regions = ocrolib.RegionExtractor()
        out = dict(columns=[], lines=[], paragraphs=[])
        exfuncs = dict(lines=regions.setPageLines,
                paragraphs=regions.setPageParagraphs)
        for box, func in exfuncs.iteritems():
            func(page_seg)
            for i in range(1, regions.length()):
                out[box].append([regions.x0(i),
                    regions.y0(i) + (regions.y1(i) - regions.y0(i)),
                    regions.x1(i) - regions.x0(i),
                    regions.y1(i) - regions.y0(i)])
        return out


class OcropusGrayscaleFilterBase(OcropusBase):
    """
    Filter a binary image.
    """
    arity = 1
    stage = stages.FILTER_GRAY

    def _eval(self):
        input = self.eval_input(0)
        return self._comp.cleanup_gray(input)


class OcropusBinaryFilterBase(OcropusBase):
    """
    Filter a binary image.
    """
    arity = 1
    stage = stages.FILTER_BINARY

    def _eval(self):
        input = self.eval_input(0)
        return self._comp.cleanup(input)


class OcropusRecognizerNode(node.Node):
    """
    Recognize an image using Ocropus.
    """
    name = "Ocropus::OcropusRecognizer"
    description = "Ocropus Native Text Recognizer"
    stage = stages.RECOGNIZE
    arity = 2
    _parameters = [
        {
            "name": "character_model",
            "value": "Ocropus Default Char"
        }, {
            "name": "language_model",
            "value": "Ocropus Default Lang",
        }
    ]

    def _eval(self):
        """
        Recognize page text.

        input: tuple of binary, input boxes
        return: page data
        """
        binary = self.eval_input(0)
        boxes = self.eval_input(1)
        pageheight, pagewidth = binary.shape
        iulibbin = ocrolib.numpy2narray(binary)
        out = dict(
                lines=[],
                box=[0, 0, pagewidth, pageheight],
        )
        for i in range(len(boxes.get("lines", []))):
            coords = boxes.get("lines")[i]
            iulibcoords = (
                coords[0], pageheight - coords[1], coords[0] + coords[2],
                pageheight - (coords[1] - coords[3]))
            lineimage = ocrolib.iulib.bytearray()
            ocrolib.iulib.extract_subimage(lineimage, iulibbin, *iulibcoords)
            out["lines"].append(dict(
                    box=coords,
                    text=self.get_transcript(ocrolib.narray2numpy(lineimage)),
            ))
        return out

    def init_converter(self):
        """
        Load the line-recogniser and the lmodel FST objects.
        """
        try:
            self._linerec = ocrolib.RecognizeLine()
            cmodpath = plugins.lookup_model_file(self._params["character_model"])
            self.logger.info("Loading file: %s" % cmodpath)
            self._linerec.load_native(cmodpath)
            self._lmodel = ocrolib.OcroFST()
            lmodpath = plugins.lookup_model_file(self._params["language_model"])
            self.logger.info("Loading file: %s" % lmodpath)
            self._lmodel.load(lmodpath)
        except (StandardError, RuntimeError):
            raise

    @plugins.check_aborted
    def get_transcript(self, line):        
        """
        Run line-recognition on an ocrolib.iulib.bytearray images of a
        single line.
        """        
        if not hasattr(self, "_lmodel"):
            self.init_converter()
        fst = self._linerec.recognizeLine(line)
        # NOTE: This returns the cost - not currently used
        out, _ = ocrolib.beam_search_simple(fst, self._lmodel, 1000)
        return out



class Manager(manager.StandardManager):
    """
    Interface to ocropus.
    """
    _use_types = (
        "IBinarize",
        "ISegmentPage",
        "ICleanupGray",
        "ICleanupBinary",
    )
    _ignored = (
        "StandardPreprocessing",
    )

    @classmethod
    def get_components(cls, oftypes=None, withnames=None, exclude=None):
        """
        Get a datastructure contraining all Ocropus components
        (possibly of a given type) and their default parameters.
        """
        out = cls._get_native_components(oftypes, withnames, exclude=exclude)
        out.extend(cls._get_python_components(oftypes, withnames, exclude=exclude))
        return out
    
    
    @classmethod
    def get_node(cls, name, **kwargs):
        """
        Get a node by the given name.
        """
        klass = cls.get_node_class(name)
        return klass(**kwargs)

    @classmethod
    def get_node_class(cls, name, comps=None):
        """
        Get a node class for the given name.
        """
        # if we get a qualified name like
        # Ocropus::Recognizer, remove the
        # path, since we ASSume that we're
        # looking in the right module
        if name.find("::") != -1:
            name = name.split("::")[-1]

        if name == "OcropusRecognizer":
            return OcropusRecognizerNode
        elif name == "FileIn":
            return OcropusFileInNode
        # FIXME: This clearly sucks
        comp = None
        if comps is not None:
            for c in comps:
                if name == c.__class__.__name__:
                    comp = c
                    break
        else:
            comp = getattr(ocrolib, name)()
        if node is None:
            raise plugins.NoSuchNodeException(name)

        base = OcropusBase
        if comp.interface() == "IBinarize":
            base = OcropusBinarizeBase
        elif comp.interface() == "ISegmentPage":
            base = OcropusSegmentPageBase
        elif comp.interface() == "ICleanupGray":
            base = OcropusGrayscaleFilterBase
        elif comp.interface() == "ICleanupBinary":
            base = OcropusBinaryFilterBase
        else:
            raise UnknownOcropusNodeType(name, comp.interface())
        # this is a bit weird
        # create a new class with the name '<OcropusComponentName>Node'
        # and the component as the inner _comp attribute
        return type("%sNode" % comp.__class__.__name__,
                    (base,), 
                    dict(_comp=comp, description=comp.description(),
                        name="Ocropus::%s" % comp.__class__.__name__))

    @classmethod
    def get_nodes(cls, *oftypes, **kwargs):
        """
        Get nodes of the given type.
        """
        kwargs.update(dict(globals=globals()))
        nodes = super(Manager, cls).get_nodes(*oftypes, **kwargs)
        rawcomps = cls.get_components(oftypes=cls._use_types, exclude=cls._ignored)
        for comp in rawcomps:
            n = cls.get_node_class(comp.__class__.__name__, comps=rawcomps)
            if len(oftypes) > 0:
                if n.stage not in oftypes:
                    continue
            nodes.append(n)
        return nodes


    @classmethod
    def _get_native_components(cls, oftypes=None, withnames=None, exclude=None):
        """
        Get a datastructure contraining all Ocropus native components
        (possibly of a given type) and their default parameters.
        """
        out = []
        clist = ocrolib.ComponentList()
        for i in range(clist.length()):
            ckind = clist.kind(i)
            if oftypes and not \
                    ckind.lower() in [c.lower() for c in oftypes]:
                continue
            cname = clist.name(i)
            if withnames and not \
                    cname.lower() in [n.lower() for n in withnames]:
                continue
            if exclude and cname.lower() in [n.lower() for n in exclude]:
                continue
            compdict = dict(name=cname, type=ckind, parameters=[])
            # TODO: Fix this heavy-handed exception handling which is
            # liable to mask genuine errors - it's needed because of
            # various inconsistencies in the Python/native component
            # wrappers.
            try:
                comp = getattr(ocrolib, cname)()
            except (AttributeError, AssertionError, IndexError):
                continue
            out.append(comp)
        return out

    @classmethod
    def _get_python_components(cls, oftypes=None, withnames=None, exclude=None):
        """
        Get native python components.
        """
        out = []
        directory = os.path.join(os.path.dirname(__file__), "tools/components")
        for fname in os.listdir(directory):
            if not fname.endswith(".py"):
                continue
            if not directory in sys.path:
                sys.path.insert(0, directory)
            modname = fname.replace(".py", "", 1)
            pmod = __import__("%s" % modname, fromlist=["main_class"])
            if not hasattr(pmod, "main_class"):
                continue
            ctype = pmod.main_class()
            ckind = ctype.__base__.__name__
            # note: the loading function in ocropy/components.py expects
            # python components to have a module-qualified name, i.e:
            # mymodule.MyComponent.
            cname = ctype.__name__
            if oftypes and not \
                    ckind.lower() in [c.lower() for c in oftypes]:
                continue
            if withnames and not \
                    cname.lower() in [n.lower() for n in withnames]:
                continue
            if exclude and cname.lower() in [n.lower() for n in exclude]:
                continue
            out.append(ctype())
        return out



