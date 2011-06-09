// Widget representing a single OCR batch.  Displays a lazy
// loading scrollable list of tasks which can be filtered 
// and individually restarted/aborted.


OCRJS.ExportWidget = OCRJS.BatchWidget.extend({
    constructor: function(parent, batch_id, initial, options) {
        this.base(parent, batch_id, initial, options);
        this._batchclass = "fedora";
        this._viewurl = null;
        this._viewtext = "View Objects";
        this._exporturl = null;
    },
});
