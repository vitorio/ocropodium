

var OcrJs = OcrJs || {};
var NT = OcrJs.Nodetree || {};


OcrJs.Nodetree.ContextMenu = OcrJs.Base.extend({
    init: function(parent, canvas) {
        this.parent = parent;
        this.canvas = canvas;
        this._menutemplate = $.template($("#nodeMenuTmpl"));
        this._context = null;

        this._listeners = {
            newNodeClicked: [],
            nodeDelete: [],
            nodeRefresh: [],
        };
    },

    startup: function(data) {
        this.buildNodeMenu(data);
    },

    setupMenuEvents: function() {
        var self = this;
        this._menu.find("li").hover(function(event) {
            $(this).addClass("ui-selected");
        }, function(event) {
            $(this).removeClass("ui-selected");
        });
        this._menu.find("li.topmenu").hoverIntent(
            function(event) {
                self._menu.find("ul.submenu").hide(); 
                self.showSubContextMenu(this, event);
            },
            function(event) {
                //$(this).find("ul").delay(1000).hide();
            }
        );

        this._menu.find("#delete_node").click(function(event) {
            self.trigger("nodeDelete", self._context);
            self.hideContextMenu();
        });
        this._menu.find("#refresh_node").click(function(event) {
            self.trigger("nodeRefresh", self._context);
            self.hideContextMenu();
        });
        this._menu.find(".topmenu").find("li").click(function(event) {
            self.trigger("newNodeClicked", event, $(this).data("name"),
                    self._context);
            self.hideContextMenu();
            event.stopPropagation();
            event.preventDefault();
        });
    },

    showContextMenu: function(event, context) {
        var self = this;
        this._context = context;
        this._menu.find("#node_context").toggle(context instanceof NT.Node);
        this._menu.find("ul.submenu").removeClass("opensubmenu").hide(); 
        this._menu.show();
        var maxx = $(this.canvas).offset().left + $(this.canvas).width(),
            maxy = $(this.canvas).offset().top + $(this.canvas).height(),
            left = event.pageX,
            top = event.pageY;
        if (event.pageX + this._menu.outerWidth() > maxx)
            left = maxx - (this._menu.outerWidth() + 20);
        if (event.pageY + this._menu.outerHeight() > maxy)
            top = maxy - (this._menu.outerHeight() + 20);
        this._menu.css({
            position: "fixed",
            top: top,
            left: left,
        });
        // NB: The setTimeout here is a hacky workaround for an
        // additional click event being fired in Firefox.  I think
        // it's this issue:
        // http://stackoverflow.com/questions/1489817/jquery-liveclick-firing-for-right-click
        setTimeout(function() {
            $(document).bind("click.menuhide", function(event) {
                self.hideContextMenu();
                $(document).unbind("click.menuhide");
                event.stopPropagation();
                event.preventDefault();
            });
        });
    },

    showSubContextMenu: function(menu, event) {
        var pos = $(menu).position(),
            left = pos.left + $(menu).outerWidth() - 5,
            top = pos.top - 5;
        var sub = $(menu).find("ul").addClass("opensubsubmenu");
        sub.show();
        sub.css({left: left, top: top});
        var spanx = $(menu).offset().left + $(menu).outerWidth() + sub.outerWidth(),
            spany = $(menu).offset().top + sub.outerHeight(),
            outerx = $(this.canvas).offset().left + $(this.canvas).width(),
            outery = $(window).height();
        if (spanx > outerx)
            sub.css("left", pos.left - sub.outerWidth());
        if (spany > outery)
            sub.css("top", top - ((spany - outery) + 20));
    },

    hideContextMenu: function(event) {
        this._menu.hide();
        this._menu.find("ul.submenu").removeClass("opensubmenu").hide(); 
        this._context = null;
    },

    buildNodeMenu: function(data) {
        var self = this;
        // do some munging of the node data so we sort the menu
        // in alphabetical stage order;
        var nodedata = {};
        $.each(data, function(i, nodeinfo) {
            if (!nodedata[nodeinfo.stage])
                nodedata[nodeinfo.stage] = [];
            nodedata[nodeinfo.stage].push(nodeinfo);
        });
        var stages = $.map(nodedata, function(nodes, stage) {
            return {
                name: stage,
                nodes: nodes,
            };
        });
        stages.sort(function(a, b) {
            return a.name > b.name;
        });
        $.each(stages, function(i, s) {
            s.nodes.sort(function(a, b) {
                return a.name > b.name;
            });
        });
        this._menu = $.tmpl(this._menutemplate, {
            stages: stages,
        }).hide();
        $("body").append(this._menu);
        this.setupMenuEvents();
    },
});
