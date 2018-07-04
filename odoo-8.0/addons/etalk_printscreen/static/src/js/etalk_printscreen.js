openerp_etalk_printscreen = function(instance, m) {
    
    var _t = instance.web._t,
    QWeb = instance.web.qweb;
    
    //TODO: Bug reset link moi lan export finish
    instance.web.ListView.include({
        load_list: function () {
            var self = this;
            this._super.apply(this, arguments);
            var links = document.getElementsByClassName("oe_etalk_printscreen");
            if (links && links[0]){
                links[0].onclick = function() {
                    self.export_to_excel("excel")
                };
            }
        },
        build_excel: function(export_type, selected) {
        	var self = this;
        	// Find Header Element
            //header_eles = self.$el.find('.oe_list_header_columns')
        	//Fix for dynamic header
        	header_eles = self.$el.find('div > div > table > thead > .oe_list_header_columns')
            header_name_list = []
            $.each(header_eles,function(){
                $header_ele = $(this)
                header_td_elements = $header_ele.find('th')
                $.each(header_td_elements,function(){
                    $header_td = $(this)
                    text = $header_td.text().trim() || ""
                    data_id = $header_td.attr('data-id')
                    if (text && !data_id){
                        data_id = 'group_name'
                    }
                    header_name_list.push({'header_name': text.trim(), 'header_data_id': data_id})
                   // }
                });
            });
            
            //Find Data Element
            data_eles = self.$el.find('.oe_list_content > tbody > tr')
            export_data = []
            $.each(data_eles,function(){
                $data_ele = $(this);
                if (selected) {
                	if ($data_ele.find('.oe_list_record_selector > input')[0] && !$data_ele.find('.oe_list_record_selector > input')[0].checked){
                		return true;
                	}
                };
            	data = [];
                is_analysis = false;
                if ($data_ele.text().trim()){
                //Find group name
	                group_th_eles = $data_ele.find('th')
	                $.each(group_th_eles,function(){
	                    $group_th_ele = $(this)
	                    text = $group_th_ele.text()
	                    is_analysis = true
	                    data.push({'data': text, 'bold': true})
	                });
	                data_td_eles = $data_ele.find('td')
	                $.each(data_td_eles,function(){
	                    $data_td_ele = $(this)
	                    text = $data_td_ele.text().trim() || "";
	                    if ($data_td_ele && $data_td_ele[0].classList.contains('oe_number') && !$data_td_ele[0].classList.contains('oe_list_field_float_time')){
	                        text = text.replace('%', '');
	                        text = instance.web.parse_value(text, { type:"float" });
	                        data.push({'data': text || "", 'number': true});
	                    }else if ($data_td_ele && $data_td_ele[0].classList.contains('oe_list_field_boolean')){
	                        value_text = 'FALSE';
	                    	text = $data_td_ele[0].childNodes[0].checked;
	                        if (text === true) {
	                        	value_text = 'TRUE';
	                        };
	                        data.push({'data': value_text});
	                    }
	                    else{
	                        data.push({'data': text});
	                    }
	                });
	                export_data.push(data);
                };
            });
            
            //Find Footer Element
            
            footer_eles = self.$el.find('.oe_list_content > tfoot> tr')
            $.each(footer_eles,function(){
                data = []
                $footer_ele = $(this)
                footer_td_eles = $footer_ele.find('td')
                $.each(footer_td_eles,function(){
                    $footer_td_ele = $(this)
                    text = $footer_td_ele.text().trim() || ""
                    if ($footer_td_ele && $footer_td_ele[0].classList.contains('oe_number')){
                        text = instance.web.parse_value(text, { type:"float" })
                        data.push({'data': text || "", 'bold': true, 'number': true})
                    }
                    else{
                        data.push({'data': text, 'bold': true})
                    }
                });
                export_data.push(data)
            });
            
            //Export to excel
            $.blockUI();
            if (export_type === 'excel'){
            	state = view.url_states;
                view.session.get_file({
                     url: '/web/export/zb_excel_export',
                     data: {data: JSON.stringify({
                            model : view.model,
                            headers : header_name_list,
                            rows : export_data,
                     })},
                     complete: $.unblockUI
                });
             }
        },
        export_to_excel: function(export_type) {
        	var self = this;
        	var export_type = export_type;
        	view = this.getParent();
        	selected = (self.groups.get_selection().ids.length !== 0) ? true : false;
        	if (selected) {
        		self.build_excel(export_type, selected);
        	} else {
        		//Reload All Page
                self._limit = null;
                self.page = 0;
                self.reload_content().done(function () {
                    self.build_excel(export_type, selected);
                });
        	}
        },
    });
};