openerp_etalk_timewidget = function (instance) {
    var _t = instance.web._t;
    	_lt = instance.web._lt;
    var QWeb = instance.web.qweb;
    
    instance.web.form.FieldDatetime.include({
    	render_value: function() {
    		var self = this;
    		if (self.widget === 'time') {
    			var l10n = _t.database.parameters;
    			var options = {}
    			if (self.options.format) {
    				//defaults: d/m/Y H:i:s
    				options.format = self.options.format
    			} else { options.format = l10n.date_format.replace(/%/g, '') + ' H:i:s'; }
				if (self.options.minDate) {
					minDate = new Date('1970/01/01');
					minDate.setDate(minDate.getDate() + self.options.minDate)
					minDate = _.str.sprintf(_t("-%s"), minDate.toString('yyyy/M/d'));
					options.minDate = minDate;
    			}
				if (self.options.maxDate) {
					maxDate = new Date('1970/01/01');
					maxDate.setDate(maxDate.getDate() + self.options.maxDate)
					maxDate = _.str.sprintf(_t("+%s"), maxDate.toString('yyyy/M/d'));
					options.maxDate = maxDate;
    			}
				if (self.options.allowTimes) {
					options.allowTimes = self.options.allowTimes
    			}
				if (self.options.onlyTime) {
					options.datepicker = false;
    			}
				if (self.options.minTime) {
					options.minTime = self.options.minTime;
    			}
				if (self.options.maxTime) {
					options.maxTime = self.options.maxTime;
    			}
				if (self.options.step) {
					options.step = self.options.step;
    			}
    			this.$el.find('input.oe_datepicker_master').idatetimepicker(options);
    		}
            if (!this.get("effective_readonly")) {
                this.datewidget.set_value(this.get('value'));
            } else {
                this.$el.text(this.format_value(this.get('value'), ''));
            }
    	},
        format_value: function(val, def) {
            if (this.widget === 'time') {
            	return instance.web.format_value(val, {'widget': 'datetime'}, def);
            }
            return instance.web.format_value(val, this, def);
        },
    });
    
    instance.web.form.widgets = instance.web.form.widgets.extend({
    	'time': 'instance.web.form.FieldDatetime',
    });
};