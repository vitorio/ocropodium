$(function() {

    var batch = null;
    var sideparams = null;
    var selectedtab = $.cookie("selectedtab") || 0;
    var sidebar = $("#sidebar_content");
    var header = $(".widget_header", $("#sidebar"));

    //$(".recent_batch_link").live("click", function(event) {
    //    batch.setBatchId($(this).data("pk"));    
    //    event.preventDefault();
    //});

    function loadBatchList() {
        $.ajax({
            url: "/batch/list?order_by=-created_on",
            data: {},
            dataType: "json",
            error: OCRJS.ajaxErrorHandler,
            success: function(data) {
                populateBatchList(data);
                header.text("Recent Batches");
            },
        });
    }

    function populateBatchList(data) {
        var list = $("<div></div>").addClass("recent_batches");
        var tbatch = $("<div></div>").addClass("recent_batch");
        var titem = $("<span></span>"); 
        var tlink = $("<a></a>").addClass("recent_batch_link");
        var ttran = $("<a></a>").addClass("button");
        $.each(data.object_list, function(i, batch) {
            var span = titem.clone();
            var link = tlink.clone()
                .attr("href", "/batch/show/" + batch.pk + "/")
                .data("pk", batch.pk)
                .text(batch.fields.name);
            var trans = ttran.clone()
                .attr("href", "/batch/transcript/" + batch.pk + "/")
                .css("float", "right")
                .data("pk", batch.pk)
                .text("Transcript");
            list
                .append(tbatch.clone().append(span.append(trans).append(link)))
                .textOverflow("...");        
        });
        sidebar.html(list);
    }

    function hashNavigate() {
        if (document.location.hash.match(/^(#task(\d+))/)) {
            var taskid = RegExp.$1;
            var taskpk = RegExp.$2;
            var sel = $(taskid);
            var pk = sidebar.data("task_pk");
            if (sel.length && pk != taskpk)
                sel.click();
        }
    }


    function loadTaskDetails(index, pk) {
        $.ajax({
            url: "/ocrtasks/show/" + pk + "/",
            type: "get",
            success: function(data) {
                var html = $(data);
                sidebar.data("task_pk", pk);
                var loaded = false;
                $.getJSON("/ocr/task_config/" + pk + "/", function(data) {
                    sideparams = new OCRJS.ParameterBuilder(
                            html.find("#options").get(0), data);
                    sideparams.addListeners({
                        onReadyState: function() {
                            if (!loaded) {
                                sidebar.html(html);
                                console.log("Active: ", selectedtab);
                                sidebar.find("#tabs")
                                    .accordion({
                                        collapsible: true,
                                        autoHeight: false,
                                        active: parseInt(selectedtab),
                                        change: function(event, ui) {
                                            selectedtab = ui.options.active;
                                            $.cookie("selectedtab", selectedtab); 
                                        },
                                    });
                                loaded = true;
                                header.text("Task #" + pk);
                            }
                            $(".submit_update", sidebar).attr("disabled", false);
                        },
                        onUpdateStarted: function() {
                            $(".submit_update", sidebar).attr("disabled", true);
                        }
                    });
                    sideparams.init();
                });
            },
        });
    }


    if ($("#batch_id").length) {
        batch = new OCRJS.BatchWidget($("#workspace").get(0), $("#batch_id").val());
        batch.addListeners({
            onTaskSelected: loadTaskDetails,
            onTaskDeselected: function() {
                loadBatchList();
            },
            onUpdate: hashNavigate,                                
        }).init();

        window.addEventListener("hashchange", function() {
            //hashNavigate();
        });

        $(".submit_update").live("click", function(event) {
            var button = $(this);
            button.attr("disabled", true);
            var pk = sidebar.data("task_pk");
            if (!pk)
                return;
            $.ajax({
                url: "/ocr/update_task/" + pk + "/",
                type: "post",
                data: sideparams.serializedData(),
                success: function(resp) {
                    $(button).attr("disabled", false);
                    if (button.attr("id").search("rerun") != -1) {
                        $.post("/ocrtasks/retry/" + pk + "/");
                        batch.pollForResults();
                    }
                },                                
            });
            return false;
        });
    
        if (document.location.hash.match(/^(#task(\d+))/)) {
            var selector = RegExp.$1;
            console.log("Selecting")
            $(selector).click();                        
        } else {
            loadBatchList();
        }
    }
});        


