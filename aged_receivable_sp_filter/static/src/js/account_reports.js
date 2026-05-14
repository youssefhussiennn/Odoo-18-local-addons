/** @odoo-module */

odoo.define('aged_receivable_sp_filter.account_report', function (require){

    'use strict';

    var core = require('web.core');
    var Context = require('web.Context');
    var AbstractAction = require('web.AbstractAction');
    var Dialog = require('web.Dialog');
    var datepicker = require('web.datepicker');
    var session = require('web.session');
    var field_utils = require('web.field_utils');
    var RelationalFields = require('web.relational_fields');
    var StandaloneFieldManagerMixin = require('web.StandaloneFieldManagerMixin');
    var { WarningDialog } = require("@web/legacy/js/_deprecated/crash_manager_warning_dialog");
    var Widget = require('web.Widget');

    var QWeb = core.qweb;
    var _t = core._t;

    var accountReportsWidget = require('account_reports.account_report');

    var accountReportsWidgetNew = accountReportsWidget.include({

        custom_events: {
            'value_changed': function(ev) {
                var self = this;

                self.report_options.partner_ids = ev.data.partner_ids;
                self.report_options.partner_categories = ev.data.partner_categories;

                // Salesperson Filter
                self.report_options.sales_person = ev.data.sales_person;

                // Account Filter
                self.report_options.account_ids = ev.data.account_ids;

                self.report_options.analytic_accounts = ev.data.analytic_accounts;
                self.report_options.analytic_tags = ev.data.analytic_tags;

                return self.reload().then(function () {
                    self.$searchview_buttons.find('.account_partner_filter').click();
                    self.$searchview_buttons.find('.account_analytic_filter').click();
                });
            },
        },

        render_searchview_buttons: function() {

            var M2MFiltersNew = Widget.extend(StandaloneFieldManagerMixin, {

                init: function (parent, fields) {
                    this._super.apply(this, arguments);
                    StandaloneFieldManagerMixin.init.call(this);

                    // Salesperson Filter
                    fields['sales_person'] = {
                        label: 'Salesperson',
                        modelName: 'res.users',
                        value: []
                    };

                    // Account Filter
                    fields['account_ids'] = {
                        label: 'Accounts',
                        modelName: 'account.account',
                        value: []
                    };

                    this.fields = fields;

                    this.widgets = {};
                },

                willStart: function () {
                    var self = this;
                    var defs = [this._super.apply(this, arguments)];

                    _.each(this.fields, function (field, fieldName) {
                        defs.push(self._makeM2MWidget(field, fieldName));
                    });

                    return Promise.all(defs);
                },

                start: function () {
                    var self = this;

                    var $content = $(QWeb.render("m2mWidgetTable", {
                        fields: this.fields
                    }));

                    self.$el.append($content);

                    _.each(this.fields, function (field, fieldName) {
                        self.widgets[fieldName].appendTo(
                            $content.find('#' + fieldName + '_field')
                        );
                    });

                    return this._super.apply(this, arguments);
                },

                //------------------------------------------------------------------
                // Private
                //------------------------------------------------------------------

                _confirmChange: function () {
                    var self = this;

                    var result = StandaloneFieldManagerMixin._confirmChange.apply(this, arguments);

                    var data = {};

                    _.each(this.fields, function (filter, fieldName) {
                        data[fieldName] = self.widgets[fieldName].value.res_ids;
                    });

                    this.trigger_up('value_changed', data);

                    return result;
                },

                _makeM2MWidget: function (fieldInfo, fieldName) {
                    var self = this;

                    var options = {};

                    options[fieldName] = {
                        options: {
                            no_create_edit: true,
                            no_create: true,
                        }
                    };

                    return this.model.makeRecord(fieldInfo.modelName, [{
                        fields: [{
                            name: 'id',
                            type: 'integer',
                        }, {
                            name: 'display_name',
                            type: 'char',
                        }],
                        name: fieldName,
                        relation: fieldInfo.modelName,
                        type: 'many2many',
                        value: fieldInfo.value,
                    }], options).then(function (recordID) {

                        self.widgets[fieldName] =
                            new RelationalFields.FieldMany2ManyTags(
                                self,
                                fieldName,
                                self.model.get(recordID),
                                {mode: 'edit'}
                            );

                        self._registerWidget(
                            recordID,
                            fieldName,
                            self.widgets[fieldName]
                        );
                    });
                },
            });

            var self = this;

            // Partner Filter
            if (this.report_options.partner) {

                if (!this.M2MFiltersNew) {

                    var fields = {};

                    // Partners
                    if ('partner_ids' in this.report_options) {
                        fields['partner_ids'] = {
                            label: _t('Partners'),
                            modelName: 'res.partner',
                            value: this.report_options.partner_ids.map(Number),
                        };
                    }

                    // Partner Tags
                    if ('partner_categories' in this.report_options) {
                        fields['partner_categories'] = {
                            label: _t('Tags'),
                            modelName: 'res.partner.category',
                            value: this.report_options.partner_categories.map(Number),
                        };
                    }

                    // Salesperson
                    if ('sales_person' in this.report_options) {
                        fields['sales_person'] = {
                            label: _t('Salesperson'),
                            modelName: 'res.users',
                            value: this.report_options.sales_person.map(Number),
                        };
                    }

                    // Accounts
                    if ('account_ids' in this.report_options) {
                        fields['account_ids'] = {
                            label: _t('Accounts'),
                            modelName: 'account.account',
                            value: this.report_options.account_ids.map(Number),
                        };
                    }

                    if (!_.isEmpty(fields)) {
                        this.M2MFiltersNew = new M2MFiltersNew(this, fields);

                        this.M2MFiltersNew.appendTo(
                            this.$searchview_buttons.find('.js_account_partner_m2m')
                        );
                    }

                } else {

                    this.$searchview_buttons
                        .find('.js_account_partner_m2m')
                        .append(this.M2MFiltersNew.$el);
                }
            }

            // Analytic Filter
            if (this.report_options.analytic) {

                if (!this.M2MFiltersNew) {

                    var fields = {};

                    if (this.report_options.analytic_accounts) {
                        fields['analytic_accounts'] = {
                            label: _t('Accounts'),
                            modelName: 'account.analytic.account',
                            value: this.report_options.analytic_accounts.map(Number),
                        };
                    }

                    if (this.report_options.analytic_tags) {
                        fields['analytic_tags'] = {
                            label: _t('Tags'),
                            modelName: 'account.analytic.tag',
                            value: this.report_options.analytic_tags.map(Number),
                        };
                    }

                    if (!_.isEmpty(fields)) {

                        this.M2MFiltersNew = new M2MFiltersNew(this, fields);

                        this.M2MFiltersNew.appendTo(
                            this.$searchview_buttons.find('.js_account_analytic_m2m')
                        );
                    }

                } else {

                    this.$searchview_buttons
                        .find('.js_account_analytic_m2m')
                        .append(this.M2MFiltersNew.$el);
                }
            }
        },
    });
});