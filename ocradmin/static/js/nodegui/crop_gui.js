//
// GUI for crop node
//

var OCRJS = OCRJS || {};
OCRJS.NodeGui = OCRJS.NodeGui || {}

OCRJS.NodeGui.CropGui = OCRJS.NodeGui.BaseGui.extend({
    constructor: function(viewer) {
        this.base(viewer, "cropgui");

        this.nodeclass = "pil.PilCrop";
        this._coords = {
            x0: -1,
            y0: -1,
            x1: -1,
            y1: -1,
        };
        this.registerListener("onCanvasChanged");
        this._node = null;

        this._color = "#FFBBBB";
        this._css = {
            borderColor: "red",
            borderWidth: 0,
            borderStyle: "solid",                    
            zIndex: 201,
            backgroundColor: this._color,
            opacity: 0.3,
        };
        this.setCanvasDraggable();        
    },

    readNodeData: function(node) {
        var coords = this._coords;                      
        $.each(node.parameters, function(i, param) {
            if (coords[param.name])
                coords[param.name] = parseInt(param.value);            
        });
        return coords;
    },                      

    sanitiseInputCoords: function(coords) {
        var fulldoc = this.sourceDimensions();
        return {
            x0: Math.max(0, Math.min(fulldoc.x, coords.x0)),
            y0: Math.max(0, Math.min(fulldoc.y, coords.y0)),
            x1: (coords.x1 < 0 ? fulldoc.x : Math.min(fulldoc.x, coords.x1)),
            y1: (coords.y1 < 0 ? fulldoc.y : Math.min(fulldoc.y, coords.y1)),
        }
    },

    sanitiseOutputCoords: function(coords) {
        var fulldoc = this.sourceDimensions();
        return {
            x0: Math.round(Math.max(-1, Math.min(coords.x0, fulldoc.x))),
            y0: Math.round(Math.max(-1, Math.min(coords.y0, fulldoc.y))),
            x1: Math.round(Math.max(-1, Math.min(coords.x1, fulldoc.x))),
            y1: Math.round(Math.max(-1, Math.min(coords.y1, fulldoc.y))),
        }
    },

    draggedRect: function(rect) {
        this.updateElement(this._rect, rect);
        this.updateNodeParameters(rect);
    },                     

    setup: function(node) {                       
        if (this._node)
            return;        
        this.base();
        var self = this;
        this._node = node;        
        console.log("Setting up crop GUI");
        var rect = this.readNodeData(node);
        this._rect = this.addTransformableRect(rect, this._css, function(newpos) {
            self.updateNodeParameters(newpos); 
        });
    },

    update: function() {
        if (!this._node)
            console.error("Gui update called with no current node");
        this.updateTransformableRect(this._rect, this.readNodeData(this._node));
    },                

    tearDown: function() {
        this.base();                  
        console.log("Tearing down crop gui");                  
        this.removeTransformableRect(this._rect);
        this._rect = null;        
        this._node = null;
    },                  

    updateNodeParameters: function(srcrect) {
        this.callListeners("parametersSet", this._node, this.sanitiseOutputCoords(srcrect));
    },                             
});
