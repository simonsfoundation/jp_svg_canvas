
// imitating ipywidgets/docs/source/examples/Custom Widget - Hello World.ipynb

//require(["widgets/js/widget", "widgets/js/manager"], function(widget, manager){

require.undef("SVGCanvas");

define("SVGCanvas", ["jupyter-js-widgets"], function(widgets) {
    
    var svgEventHandlerFactory = function(that) {
        var svgEventHandler = function(e) {
            //debugger;
            var target = e.target;
            var info = {};
            for (var attr in e) {
                var val = e[attr];
                var ty = (typeof val);
                if ((ty == "number") ||
                    (ty == "string") ||
                    (ty == "boolean")) {
                    info[attr] = val;
                }
            }
            info.name = target.ipy_name;
            var ept = SVGEventLocation(that, e);
            info.svgX = ept.x;
            info.svgY = ept.y;
            var json = JSON.stringify(info);
            that.model.set("event", json);
            that.touch();
        };
        return svgEventHandler;
    };

    var SVGEventLocation = function(that, e) {
        // http://stackoverflow.com/questions/10298658/mouse-position-inside-autoscaled-svg
        var pt = that.reference_point;
        var svg = that.$svg[0];
        pt.x = e.clientX;
        pt.y = e.clientY;
        return pt.matrixTransform(svg.getScreenCTM().inverse());
    }
    
    var SVGCanvasView = widgets.DOMWidgetView.extend({
        
        render: function() {
            var that = this;
            var svg = that.svg_elt("svg");
            var eventHandler = svgEventHandlerFactory(that);
            that.eventHandler = eventHandler;
            that.named_elements = {};
            svg.ipy_name = "";
            that.$svg = $(svg);
            that.reference_point = svg.createSVGPoint();
            svg.setAttribute("preserveAspectRatio", "none");
            that.$el.append(that.$svg);
            that.svg_parameters_changed();
            that.commands_changed();
            that.start_watch_event();
            that.model.on("change:commands", that.commands_changed, that);
            that.model.on("change:viewBox", that.svg_parameters_changed, that);
            that.model.on("change:width", that.svg_parameters_changed, that);
            that.model.on("change:height", that.svg_parameters_changed, that);
            that.model.on("change:style", that.svg_parameters_changed, that);
            that.model.on("change:watch_event", that.start_watch_event, that);
            that.model.on("change:unwatch_event", that.stop_watch_event, that);
        },
        
        start_watch_event: function() {
            //debugger;
            var that = this;
            var event_types = that.model.get("watch_event");
            if (event_types != "") {
                that.$svg.on(event_types, that.eventHandler);
                that.model.set("watch_event", "");
                that.touch();
            }
        },
        
        stop_watch_event: function() {
            //debugger;
            var that = this;
            var event_types = that.model.get("unwatch_event");
            if (event_types != "") {
                that.$svg.off(event_types);
                that.model.set("watch_event", "");
                that.touch();
            }
        },
        
        commands_changed: function() {
            var that = this;
            var svg = that.$svg[0];
            var commands = that.get_JSON("commands")
            for (var i=0; i<commands.length; i++) {
                var command_dict = commands[i];
                var indicator = command_dict["command"];
                var method = that["do_"+indicator];
                method(that, command_dict);
            }
        },

        do_fit: function(that, info) {
            // fit viewport to bounding box.
            var svg = that.$svg[0];
            var bbox = svg.getBBox();
            var D = {"width": bbox.width, "height": bbox.height, "x": bbox.x, "y": bbox.y}
            var vbox = "" + D.x + " " + D.y + " " + D.width + " " + D.height;
            if ((D.width > 0) && (D.height > 0)) {
                that.model.set("boundingBox", D);
                if (info.changeView) {
                    that.model.set("viewBox", vbox);
                }
                // Element viewBox will be updated later by model change.
                that.touch();
            }
        },
        
        do_add_element: function (that, info) {
            //debugger;
            var tag = info.tag;
            var name = info.name;
            var element = that.svg_elt(tag);
            element.ipy_name = name;
            var $element = $(element);
            that.update_element($element, info);
            // add event callbacks
            that.$svg.append($element);
            that.named_elements[name] = $element;
        },
        
        do_change_element: function (that, info) {
            var name = info.name;
            var $element = that.named_elements[name];
            if ($element) {
                that.update_element($element, info);
            } else {
                console.warn("couldn't find element for "+name);
            }
        },
        
        do_delete: function (that, info) {
            var names = info.names;
            for (var i=0; i<names.length; i++) {
                var name = names[i];
                var $element = that.named_elements[name];
                if ($element) {
                    $element.remove();
                    delete that.named_elements[name];
                }
            }
        },
        
        update_element: function($element, info) {
            var element = $element[0];
            var atts = info.atts;
            var style = info.style;
            var text = info.text;
            if (atts) {
                for (var att in atts) {
                    element.setAttribute(att, atts[att]);
                }
            }
            if (style) {
                for (var styling in style) {
                    element.style[styling] = style[styling];
                }
            }
            if (text) {
                $element.empty();
                var node = document.createTextNode(text);
                element.appendChild(node);
            }
        },
        
        do_empty: function (that, info) {
            that.named_elements = {};
            that.$svg.empty();
        },
        
        svg_parameters_changed: function() {
            var that = this;
            var style_additions = that.get_JSON("style");
            var svg = that.$svg[0];
            //debugger;
            svg.setAttribute("viewBox", that.model.get("viewBox"));
            svg.setAttribute("width", that.model.get("width"));
            svg.setAttribute("height", that.model.get("height"));
            for (var style_attr in style_additions) {
                svg.style[style_attr] = style_additions[style_attr];
            }
        },
        
        get_JSON: function(name) {
            var json = this.model.get(name);
            return $.parseJSON(json);
        },
        
        svg_elt: function(kind) {
            return document.createElementNS('http://www.w3.org/2000/svg', kind);
        }
        
    });
    
    //manager.WidgetManager.register_widget_view('SVGCanvasView', SVGCanvasView);
    return {
        SVGCanvasView: SVGCanvasView
    }
});
