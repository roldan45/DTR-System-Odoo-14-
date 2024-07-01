odoo.define('payroll.ProgressBarNew', function (require) {
    "use strict";

    var AbstractField = require('web.AbstractField');
    var field_registry = require('web.field_registry');
    var core = require('web.core');
    var _t = core._t;

    var ProgressBarNew = AbstractField.extend({
        template: "NewProgressBar",
        supportedFieldTypes: ['integer', 'float'],

        start: function () {
            this._super.apply(this, arguments);

            if (this.recordData[this.nodeOptions.currentValue]) {
                this.value = this.recordData[this.nodeOptions.currentValue];
            }

            this.editable_readonly = !!this.nodeOptions.editable_readonly;
            this.readonly = this.nodeOptions.readonly || !this.nodeOptions.editable;
            this.canWrite = !this.readonly && (
                this.mode === 'edit' ||
                (this.editable_readonly && this.mode === 'readonly') ||
                (this.viewType === 'kanban')
            );

            this.edit_max_value = !!this.nodeOptions.edit_max_value;
            this.max_value = this.recordData[this.nodeOptions.max_value] || 100;

            this.title = _t(this.attrs.title || this.nodeOptions.title) || '';

            this.write_mode = false;
        },

        _render: function () {
            var self = this;
            this._render_value();

            if (this.canWrite) {
                if (this.edit_on_click) {
                    this.$el.on('click', '.o_progress', function (e) {
                        var $target = $(e.currentTarget);
                        var numValue = Math.floor((e.pageX - $target.offset().left) / $target.outerWidth() * self.max_value);
                        self.on_update(numValue);
                        self._render_value();
                    });
                } else {
                    this.$el.on('click', function () {
                        if (!self.write_mode) {
                            var $input = $('<input>', { type: 'text', class: 'o_progressbar_value o_input' });
                            $input.on('blur', self.on_change_input.bind(self));
                            self.$('.o_progressbar_value').replaceWith($input);
                            self.write_mode = true;
                            self._render_value();
                        }
                    });
                }
            }
            return this._super();
        },

        on_update: function (value) {
            if (this.edit_max_value) {
                this.max_value = value;
                this._isValid = true;
                var changes = {};
                changes[this.nodeOptions.max_value] = this.max_value;
                this.trigger_up('field_changed', {
                    dataPointID: this.dataPointID,
                    changes: changes,
                });
            } else {
                var formattedValue = this._formatValue(value);
                this._setValue(formattedValue);
            }
        },

        _render_value: function (v) {
            var value = this.value || 0;
            var max_value = this.max_value || 0;

            if (!isNaN(v)) {
                if (this.edit_max_value) {
                    max_value = v;
                } else {
                    value = v;
                }
            }
//____________________________________________________________
            var widthComplete = Math.min((value / max_value) * 100, 100); 

            if (widthComplete >= 100) {
                this.$('.o_progressbar_complete').css('background-color', '#69B34C'); // Apple (Green)
            } else if (widthComplete >= 90 && widthComplete <= 99) {
                this.$('.o_progressbar_complete').css('background-color', '#80A64B'); // Dark Lime Green
            } else if (widthComplete >= 80 && widthComplete <= 89) {
                this.$('.o_progressbar_complete').css('background-color', '#97B04A'); // Lime Green
            } else if (widthComplete >= 70 && widthComplete <= 79) {
                this.$('.o_progressbar_complete').css('background-color', '#AEB949'); // Olive Green
            } else if (widthComplete >= 60 && widthComplete <= 69) {
                this.$('.o_progressbar_complete').css('background-color', '#C5C348'); // Dark Yellow
            } else if (widthComplete >= 50 && widthComplete <= 59) {
                this.$('.o_progressbar_complete').css('background-color', '#DCD647'); // Yellow
            } else if (widthComplete >= 40 && widthComplete <= 49) {
                this.$('.o_progressbar_complete').css('background-color', '#F4E046'); // Light Yellow
            } else if (widthComplete >= 30 && widthComplete <= 39) {
                this.$('.o_progressbar_complete').css('background-color', '#FAB733'); // Saffron
            } else if (widthComplete >= 20 && widthComplete <= 29) {
                this.$('.o_progressbar_complete').css('background-color', '#E5A72B'); // Dark Orange
            } else if (widthComplete >= 10 && widthComplete <= 19) {
                this.$('.o_progressbar_complete').css('background-color', '#CB8C24'); // Orange
            } else {
                this.$('.o_progressbar_complete').css('background-color', '#FF0D0D'); // Candy Apple Red
            }
            
            
            


            this.$('.o_progress').toggleClass('o_progress_overflow', value > max_value)
                .attr('aria-valuemin', '0')
                .attr('aria-valuemax', max_value)
                .attr('aria-valuenow', value);

            this.$('.o_progressbar_complete').css('width', widthComplete + '%');

        },

        _reset: function () {
            this._super.apply(this, arguments);
            var new_max_value = this.recordData[this.nodeOptions.max_value];
            this.max_value = new_max_value !== undefined ? new_max_value : this.max_value;
        },

        isSet: function () {
            return true;
        },
    });

    field_registry.add('progress_bar_new', ProgressBarNew);
});
