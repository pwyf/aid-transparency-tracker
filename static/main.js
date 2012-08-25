(function() {
  var DEFAULT_FIELD_SETUP, DEFAULT_MODEL, DIMENSION_META, Delegator, DimensionWidget, DimensionsWidget, FIELDS_META, ModelEditor, SAMPLE_DATA, UniqueKeyWidget, Widget, util;
  var __slice = Array.prototype.slice, __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; }, __hasProp = Object.prototype.hasOwnProperty, __extends = function(child, parent) {
    for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; }
    function ctor() { this.constructor = child; }
    ctor.prototype = parent.prototype;
    child.prototype = new ctor;
    child.__super__ = parent.prototype;
    return child;
  }, __indexOf = Array.prototype.indexOf || function(item) {
    for (var i = 0, l = this.length; i < l; i++) {
      if (this[i] === item) return i;
    }
    return -1;
  };
  Delegator = (function() {
    Delegator.prototype.events = {};
    Delegator.prototype.options = {};
    Delegator.prototype.element = null;
    function Delegator(element, options) {
      this.options = $.extend(true, {}, this.options, options);
      this.element = $(element);
      this.on = this.subscribe;
      this.addEvents();
    }
    Delegator.prototype.addEvents = function() {
      var event, functionName, sel, selector, _i, _ref, _ref2, _results;
      _ref = this.events;
      _results = [];
      for (sel in _ref) {
        functionName = _ref[sel];
        _ref2 = sel.split(' '), selector = 2 <= _ref2.length ? __slice.call(_ref2, 0, _i = _ref2.length - 1) : (_i = 0, []), event = _ref2[_i++];
        _results.push(this.addEvent(selector.join(' '), event, functionName));
      }
      return _results;
    };
    Delegator.prototype.addEvent = function(bindTo, event, functionName) {
      var closure, isBlankSelector;
      closure = __bind(function() {
        return this[functionName].apply(this, arguments);
      }, this);
      isBlankSelector = typeof bindTo === 'string' && bindTo.replace(/\s+/g, '') === '';
      if (isBlankSelector) {
        bindTo = this.element;
      }
      if (typeof bindTo === 'string') {
        this.element.delegate(bindTo, event, closure);
      } else {
        if (this.isCustomEvent(event)) {
          this.subscribe(event, closure);
        } else {
          $(bindTo).bind(event, closure);
        }
      }
      return this;
    };
    Delegator.prototype.isCustomEvent = function(event) {
      var natives;
      natives = "blur focus focusin focusout load resize scroll unload click dblclick\nmousedown mouseup mousemove mouseover mouseout mouseenter mouseleave\nchange select submit keydown keypress keyup error".split(/[^a-z]+/);
      event = event.split('.')[0];
      return $.inArray(event, natives) === -1;
    };
    Delegator.prototype.publish = function() {
      this.element.triggerHandler.apply(this.element, arguments);
      return this;
    };
    Delegator.prototype.subscribe = function(event, callback) {
      var closure;
      closure = function() {
        return callback.apply(this, [].slice.call(arguments, 1));
      };
      closure.guid = callback.guid = ($.guid += 1);
      this.element.bind(event, closure);
      return this;
    };
    Delegator.prototype.unsubscribe = function() {
      this.element.unbind.apply(this.element, arguments);
      return this;
    };
    return Delegator;
  })();
  $.plugin = function(name, object) {
    return jQuery.fn[name] = function(options) {
      var args;
      args = Array.prototype.slice.call(arguments, 1);
      return this.each(function() {
        var instance;
        instance = $.data(this, name);
        if (instance) {
          return options && instance[options].apply(instance, args);
        } else {
          instance = new object(this, options);
          return $.data(this, name, instance);
        }
      });
    };
  };
  $.a2o = function(ary) {
    var obj, walk;
    obj = {};
    walk = function(o, path, value) {
      var key;
      key = path[0];
      if (path.length === 2 && path[1] === '') {
        if ($.type(o[key]) !== 'array') {
          o[key] = [];
        }
        return o[key].push(value);
      } else if (path.length === 1) {
        return o[key] = value;
      } else {
        if ($.type(o[key]) !== 'object') {
          o[key] = {};
        }
        return walk(o[key], path.slice(1), value);
      }
    };
    $.each(ary, function() {
      var p, path;
      path = this.name.split('[');
      path = [path[0]].concat(__slice.call((function() {
          var _i, _len, _ref, _results;
          _ref = path.slice(1);
          _results = [];
          for (_i = 0, _len = _ref.length; _i < _len; _i++) {
            p = _ref[_i];
            _results.push(p.slice(0, -1));
          }
          return _results;
        })()));
      return walk(obj, path, this.value);
    });
    return obj;
  };
  $.fn.serializeObject = function() {
    var ary;
    ary = this.serializeArray();
    return $.a2o(ary);
  };
  SAMPLE_DATA = {
    "Project ID": "AGNA64",
    "Title Project": "WE CAN end violence against women in Afghanistan",
    "Short Descr Project": "The project is part of PIP P00115 which is the South Asia regional “We Can end violence against women campaign”. The objective is to challenge and change the patriarchal idea, beliefs, attitude, behaviour and practice that perpetuate violence against women. Project will take numbers of initiatives, which ultimately contribute to breaking the silence of domestic violence, which has huge prevalence all over the Afghan society. Under this project numbers of campaign initiatives will be taken to mobilise 2000 change makers and to make them aware about the issue and bring positive change in their personal attitudes, behaviours and practices.",
    "Project Starts": "1-May-07",
    "Project Ends": "31-Mar-11",
    "Level of Impact": "Country",
    "ISO CODE": "AF",
    "Loc of Impact": "Afghanistan",
    "Loc Info": " Kabul ",
    "% Aim 1: Right to Sustainable Livelihoods": "-0",
    "% Aim 2: Right to Essential services": "-0",
    "% Aim 3: Right to Life and Security": "-0",
    "% Aim 4: Right to be heard": "10",
    "% Aim 5: Right to Equity": "90",
    " Expenditure prior to 2010/11": " 95,018 ",
    "Expenditure in 2010/11": " 40,415 ",
    " Revised Budget  in current and future years (£) ": "-0",
    "Total Value all years (£)": " 135,433 "
  };
  DEFAULT_MODEL = {
    organisation: {},
    mapping: {
      'iati-identifier': {
        datatype: 'compound',
        'iati-field': 'iati-identifier',
        label: 'IATI Identifier',
        fields: {
          'text': {}
        }
      },
      'title': {
        datatype: 'compound',
        'iati-field': 'title',
        label: 'Title',
        fields: {
          'text': {}
        }
      },
      'description': {
        datatype: 'compound',
        'iati-field': 'description',
        label: 'Description',
        fields: {
          'text': {}
        }
      },
      'activity-status': {
        datatype: 'compound',
        'iati-field': 'activity-status',
        label: 'Activity Status',
        fields: {
          'code': {},
          'text': {}
        }
      },
      'activity-date-start': {
        datatype: 'compound',
        label: 'Activity Start Date',
        'iati-field': 'activity-date',
        fields: {
          'type': {
            'constant': 'start-planned',
            'datatype': 'constant'
          },
          'iso-date': {},
          'text': {}
        }
      },
      'activity-date-end': {
        datatype: 'compound',
        label: 'Activity End Date',
        'iati-field': 'activity-date',
        fields: {
          'type': {
            'constant': 'end-planned',
            'datatype': 'constant'
          },
          'iso-date': {},
          'text': {}
        }
      },
      'recipient-country': {
        datatype: 'compound',
        'iati-field': 'recipient-country',
        label: 'Recipient Country',
        fields: {
          'text': {},
          'code': {}
        }
      },
      'recipient-region': {
        datatype: 'compound',
        'iati-field': 'recipient-region',
        label: 'Recipient Region',
        fields: {
          'text': {},
          'code': {}
        }
      },
      'funding-organisation': {
        datatype: 'compound',
        'iati-field': 'participating-org',
        label: 'Funding Organisation',
        fields: {
          'role': {
            'constant': 'funding',
            'datatype': 'constant'
          },
          'text': {},
          'ref': {},
          'type': {}
        }
      },
      'extending-organisation': {
        datatype: 'compound',
        'iati-field': 'participating-org',
        label: 'Extending Organisation',
        fields: {
          'role': {
            'constant': 'extending',
            'datatype': 'constant'
          },
          'text': {},
          'ref': {},
          'type': {}
        }
      },
      'implementing-organisation': {
        datatype: 'compound',
        'iati-field': 'participating-org',
        label: 'Implementing Organisation',
        fields: {
          'role': {
            'constant': 'implementing',
            'datatype': 'constant'
          },
          'text': {},
          'ref': {},
          'type': {}
        }
      },
      sectors: {
        datatype: 'compound',
        label: 'Sectors',
        'iati-field': 'sector',
        fields: {
          'text': {
            'label': 'Name (text) of the sector'
          },
          'code': {
            'label': 'Code for the sector'
          },
          'vocab': {
            'label': 'Sector code vocabulary'
          }
        }
      },
      transaction: {
        datatype: 'transaction',
        label: 'Transactions',
        'iati-field': 'transaction',
        'tdatafields': {
          transaction_type: {
            "label": "Transaction type",
            "iati-field": "transaction-type",
            "datatype": "compound",
            "fields": {
              "text": {
                "constant": "Disbursement",
                "datatype": "constant"
              },
              "code": {
                "constant": "D",
                "datatype": "constant"
              }
            }
          },
          value: {
            "label": "Transaction value",
            "iati-field": "value",
            "datatype": "compound",
            "fields": {
              "text": {},
              "value-date": {}
            }
          },
          description: {
            "label": "Transaction Description",
            "iati-field": "description",
            "datatype": "compound",
            "fields": {
              "iso-date": {},
              "text": {}
            }
          },
          'transaction-date': {
            "label": "Transaction Date",
            "iati-field": "transaction-date",
            "datatype": "compound",
            "fields": {
              "iso-date": {},
              "text": {}
            }
          },
          'provider-org': {
            "label": "Transaction Provider",
            "iati-field": "provider-org",
            "datatype": "compound",
            "fields": {
              "text": {},
              "ref": {},
              "provider-activity-id": {}
            }
          },
          'receiver-org': {
            "label": "Transaction Receiver",
            "iati-field": "receiver-org",
            "datatype": "compound",
            "fields": {
              "text": {},
              "ref": {},
              "receiver-activity-id": {}
            }
          }
        }
      }
    }
  };
  DEFAULT_FIELD_SETUP = {
    'iati-identifier': {
      datatype: 'compound',
      label: 'IATI Identifier',
      fields: {
        'text': {
          required: true
        }
      }
    },
    'other-identifier': {
      datatype: 'compound',
      label: 'Other Identifier',
      fields: {
        'text': {
          required: true
        },
        'owner-name': {
          required: false
        },
        'owner-ref': {
          required: false
        }
      }
    },
    'title': {
      datatype: 'compound',
      label: 'Title',
      fields: {
        'text': {
          required: true
        }
      }
    },
    'description': {
      datatype: 'compound',
      label: 'Description',
      fields: {
        'text': {
          required: true
        }
      }
    },
    'activity-status': {
      datatype: 'compound',
      label: 'Activity Status',
      fields: {
        'code': {
          required: true
        },
        'text': {
          required: true
        }
      }
    },
    'activity-date': {
      datatype: 'compound',
      label: 'Activity Dates',
      fields: {
        'type': {
          required: true
        },
        'iso-date': {
          required: true
        },
        'text': {
          required: true
        }
      }
    },
    'participating-org': {
      datatype: 'compound',
      label: 'Participating Organisation',
      fields: {
        'role': {
          required: true
        },
        'ref': {
          required: false
        },
        'type': {
          required: false
        },
        'text': {
          required: true
        }
      }
    },
    'recipient-country': {
      datatype: 'compound',
      label: 'Recipient country',
      fields: {
        'code': {
          required: true
        },
        'text': {
          required: true
        },
        'percentage': {
          required: false
        }
      }
    },
    'recipient-region': {
      datatype: 'compound',
      label: 'Recipient region',
      fields: {
        'code': {
          required: true
        },
        'text': {
          required: true
        },
        'percentage': {
          required: false
        }
      }
    },
    'sector': {
      datatype: 'compound',
      label: 'Sectors',
      fields: {
        'vocabulary': {
          required: true
        },
        'code': {
          required: false
        },
        'text': {
          required: true
        },
        'percentage': {
          required: false
        }
      }
    },
    'policy-marker': {
      datatype: 'compound',
      label: 'Policy Marker',
      fields: {
        'significance': {
          required: true
        },
        'vocabulary': {
          required: true
        },
        'code': {
          required: true
        },
        'text': {
          required: true
        }
      }
    },
    'collaboration-type': {
      datatype: 'compound',
      label: 'Collaboration type',
      fields: {
        'code': {
          required: true
        },
        'text': {
          required: true
        }
      }
    },
    'default-flow-type': {
      datatype: 'compound',
      label: 'Flow type',
      fields: {
        'code': {
          required: true
        },
        'text': {
          required: true
        }
      }
    },
    'default-finance-type': {
      datatype: 'compound',
      label: 'Finance type',
      fields: {
        'code': {
          required: true
        },
        'text': {
          required: true
        }
      }
    },
    'default-aid-type': {
      datatype: 'compound',
      label: 'Aid type',
      fields: {
        'code': {
          required: true
        },
        'text': {
          required: true
        }
      }
    },
    'default-tied-status': {
      datatype: 'compound',
      label: 'Tied Aid Status',
      fields: {
        'code': {
          required: true
        },
        'text': {
          required: true
        }
      }
    },
    'transaction': {
      datatype: 'transaction',
      label: 'Transaction',
      'tdatafields': {
        'transaction-type': {
          "datatype": "compound",
          "label": "Transaction Type",
          "iati-field": "transaction-type",
          "fields": {
            "text": {
              required: true
            },
            "code": {
              required: true
            }
          }
        },
        'value': {
          "datatype": "compound",
          "label": "Transaction Value",
          "iati-field": "value",
          "fields": {
            "text": {
              required: true
            },
            "value-date": {
              required: true
            },
            "currency": {
              required: false
            }
          }
        },
        'description': {
          "datatype": "compound",
          "label": "Transaction Description",
          "iati-field": "description",
          "fields": {
            "text": {
              required: true
            }
          }
        },
        'transaction-date': {
          "datatype": "compound",
          "label": "Transaction Date",
          "iati-field": "transaction-date",
          "fields": {
            "iso-date": {
              required: true
            },
            "text": {
              required: false
            }
          }
        },
        'provider-org': {
          "datatype": "compound",
          "label": "Transaction Provider",
          "iati-field": "provider-org",
          "fields": {
            "text": {
              required: false
            },
            "ref": {
              required: false
            },
            "provider-activity-id": {
              required: false
            }
          }
        },
        'receiver-org': {
          "datatype": "compound",
          "label": "Transaction Receiver",
          "iati-field": "receiver-org",
          "fields": {
            "text": {
              required: false
            },
            "ref": {
              required: false
            },
            "receiver-activity-id": {
              required: false
            }
          }
        }
      }
    }
  };
  DIMENSION_META = {
    'iati-identifier': {
      fixedDataType: true,
      helpText: 'The unique IATI Identifier for your project. This must appear only once in the file: there can not be two activities with the same IATI Identifier. The Identifier is normally composed of the reporting organisation\'s unique reference, followed by the organisation\'s internal project code.<br />E.g. an Oxfam project would be <code>GB-CHC-202918-<b>P00001</b></code>, where <code>P0001</code> is the project code.'
    },
    'other-identifier': {
      fixedDataType: true,
      helpText: 'An activity can be defined and/or reported on by multiple organisations. All such identifiers can be reported here.'
    },
    title: {
      fixedDataType: true,
      helpText: 'A short, human-readable title. May be repeated for different languages. '
    },
    description: {
      fixedDataType: true,
      helpText: 'A longer, human-readable description. May be repeated for different languages. '
    },
    'activity-status': {
      fixedDataType: true,
      helpText: 'The current stage of the aid activity at the time the IATI information is published/updated. The stages are based on an activity lifecycle.'
    },
    'activity-date': {
      fixedDataType: true,
      helpText: 'The expected and actual start and completion dates of the activity, where start is the date of first disbursement for the activity and completion is the date of last disbursement for the activity.'
    },
    'participating-org': {
      fixedDataType: true,
      helpText: 'Organisations involved the project. Roles available for participating organisations are <code>funding</code>, <code>extending</code> and <code>implementing</code>.'
    },
    'recipient-country': {
      fixedDataType: true,
      helpText: 'The country(ies) for whose benefit the aid flow is provided, if applicable. Repeat for each country where known.'
    },
    'recipient-region': {
      fixedDataType: true,
      helpText: 'Supra-national: The geographical or administrative region grouping various countries (e.g. Sub-Saharan Africa, Mekong Delta). Use ‘global’ for activities benefiting substantially all developing countries. If percentages are shown for each region they must add to 100% for the activity being reported.'
    },
    sector: {
      fixedDataType: true,
      helpText: 'The specific area(s) of the recipient\'s economic or social development that the transfer intends to foster. Also known as purpose codes.'
    },
    'policy-marker': {
      fixedDataType: true,
      helpText: 'Indicators tracking key policy issues. This can be also used for donor specific thematic classifications.'
    },
    'collaboration-type': {
      fixedDataType: true,
      helpText: 'Identifier to show the type of collaboration. For official donors, shows if the activity is bilateral; earmarked multilateral; core multilateral; core contributions to NGOs; core contributions to PPPs; or multilateral outflow. Allows for additional types that might apply to foundations and NGOs. '
    },
    'default-flow-type': {
      fixedDataType: true,
      helpText: 'Identifier to show the classification of the flow. For official donors if the activity is Official Development Assistance (ODA), or Other Official Flows (OOF) [non-concessional but developmental, i.e. excluding export credits]. Allows for any types that might apply to foundations and NGOs. Default flow type can be overridden by flow type on any specific transaction within the activity.'
    },
    'default-finance-type': {
      fixedDataType: true,
      helpText: 'Identifier to show the financing mechanism of the aid activity (e.g. grant, loan, capital subscription, export credit, debt relief, equity). Default finance type can be overridden by finance type on any specific transaction within the activity.'
    },
    'default-aid-type': {
      fixedDataType: true,
      helpText: 'Identifier to show the type of assistance provided. For official donors broad categories are budget support, pooled funds, project-type interventions, experts, scholarships, debt relief, administrative costs). Allows for any types that might apply to private donors. Default aid type can be overridden by aid type on any specific transaction within the activity.'
    },
    'default-tied-status': {
      fixedDataType: true,
      helpText: 'Amounts by degree of restriction on where procurement of goods or services can take place, classified as untied (open procurement), partially tied (donor and developing countries) and tied (donor or group not including most developing countries). Note that there is both a default for the entire activity, and an optional status for each transaction, for when different contributions to an activity have different tied statuses.'
    },
    transaction: {
      fixedDataType: true,
      helpText: 'Details of each financial transaction by the donor.'
    }
  };
  FIELDS_META = {
    label: {
      required: true
    }
  };
  String.prototype.dasherize = function() {
    return this.replace(/_/g, "-");
  };
  util = {
    flattenObject: function(obj) {
      var flat, pathStr, walk;
      flat = {};
      pathStr = function(path) {
        var ary, p;
        ary = [path[0]];
        ary = ary.concat((function() {
          var _i, _len, _ref, _results;
          _ref = path.slice(1);
          _results = [];
          for (_i = 0, _len = _ref.length; _i < _len; _i++) {
            p = _ref[_i];
            _results.push("[" + p + "]");
          }
          return _results;
        })());
        return ary.join('');
      };
      walk = function(path, o) {
        var key, newpath, value, _results;
        _results = [];
        for (key in o) {
          value = o[key];
          newpath = $.extend([], path);
          newpath.push(key);
          _results.push($.type(value) === 'object' ? walk(newpath, value) : ($.type(value) === 'array' ? newpath.push('') : void 0, flat[pathStr(newpath)] = value));
        }
        return _results;
      };
      walk([], obj);
      return flat;
    }
  };
  Widget = (function() {
    __extends(Widget, Delegator);
    function Widget() {
      Widget.__super__.constructor.apply(this, arguments);
    }
    Widget.prototype.deserialize = function(data) {};
    return Widget;
  })();
  UniqueKeyWidget = (function() {
    __extends(UniqueKeyWidget, Widget);
    function UniqueKeyWidget() {
      UniqueKeyWidget.__super__.constructor.apply(this, arguments);
    }
    UniqueKeyWidget.prototype.events = {
      'span click': 'onKeyClick'
    };
    UniqueKeyWidget.prototype.deserialize = function(data) {
      var availableKeys, fk, fv, k, uniq, v, _ref, _ref2, _ref3;
      uniq = ((_ref = data['dataset']) != null ? _ref['unique_keys'] : void 0) || [];
      availableKeys = [];
      _ref2 = data['mapping'];
      for (k in _ref2) {
        v = _ref2[k];
        if (v['datatype'] !== 'value') {
          _ref3 = v['fields'];
          for (fk in _ref3) {
            fv = _ref3[fk];
            availableKeys.push("" + k + "." + fk);
          }
        } else {
          availableKeys.push(k);
        }
      }
      this.keys = (function() {
        var _i, _len, _results;
        _results = [];
        for (_i = 0, _len = availableKeys.length; _i < _len; _i++) {
          k = availableKeys[_i];
          _results.push({
            'name': k,
            'used': __indexOf.call(uniq, k) >= 0
          });
        }
        return _results;
      })();
      return this.render();
    };
    UniqueKeyWidget.prototype.promptAddDimensionNamed = function(props, thename) {
      return false;
    };
    UniqueKeyWidget.prototype.render = function() {
      return this.element.html($.tmpl('tpl_unique_keys', {
        'keys': this.keys
      }));
    };
    UniqueKeyWidget.prototype.onKeyClick = function(e) {
      var idx;
      idx = this.element.find('span').index(e.currentTarget);
      this.keys[idx]['used'] = !this.keys[idx]['used'];
      this.render();
      return this.element.parents('form').first().change();
    };
    return UniqueKeyWidget;
  })();
  DimensionWidget = (function() {
    __extends(DimensionWidget, Widget);
    DimensionWidget.prototype.events = {
      '.add_field click': 'onAddFieldClick',
      '.field_switch_constant click': 'onFieldSwitchConstantClick',
      '.field_switch_column click': 'onFieldSwitchColumnClick',
      '.field_switch_constant_transaction click': 'onFieldSwitchConstantClickTransaction',
      '.field_switch_column_transaction click': 'onFieldSwitchColumnClickTransaction',
      '.field_rm click': 'onFieldRemoveClick',
      '.delete_dimension click': 'onDeleteDimensionClick',
      '.delete_tdatafield click': 'onDeleteTDataFieldClick',
      '.iatifield change': 'onIATIFieldChange',
      '.column change': 'onColumnChange'
    };
    function DimensionWidget(name, container, options) {
      this.formFieldRequired2 = __bind(this.formFieldRequired2, this);
      this.formFieldRequired = __bind(this.formFieldRequired, this);
      this.formFieldTransactionPrefix = __bind(this.formFieldTransactionPrefix, this);
      this.formFieldPrefix = __bind(this.formFieldPrefix, this);      var el;
      this.name = name;
      el = $("<fieldset class='dimension' data-dimension-name='" + this.name + "'>            </fieldset>").appendTo(container);
      DimensionWidget.__super__.constructor.call(this, el, options);
      this.id = "" + (this.element.parents('.modeleditor').attr('id')) + "_dim_" + this.name;
      this.element.attr('id', this.id);
    }
    DimensionWidget.prototype.deserialize = function(data) {
      var formObj, k, v, _ref, _ref2, _ref3, _results;
      this.data = ((_ref = data['mapping']) != null ? _ref[this.name] : void 0) || {};
      this.iati_field = ((_ref2 = data['mapping']) != null ? _ref2[this.name]['iati-field'] : void 0) || '';
      this.meta = DIMENSION_META[this.iati_field] || {};
      if (this.data.datatype !== 'value' && !('fields' in this.data)) {
        this.data.fields = {
          'label': {
            'datatype': 'string'
          }
        };
      }
      this.element.html($.tmpl('tpl_dimension', this));
      this.element.trigger('fillColumnsRequest', [this.element.find('select.column')]);
      this.element.trigger('fillIATIfieldsRequest', [this.element.find('select.iatifield')]);
      formObj = {
        'mapping': {}
      };
      formObj['mapping'][this.name] = this.data;
      _ref3 = util.flattenObject(formObj);
      _results = [];
      for (k in _ref3) {
        v = _ref3[k];
        _results.push(this.element.find("[name=\"" + k + "\"]").val(v));
      }
      return _results;
    };
    DimensionWidget.prototype.formFieldPrefix = function(fieldName) {
      return "mapping[" + this.name + "][fields][" + fieldName + "]";
    };
    DimensionWidget.prototype.formFieldTransactionPrefix = function(fieldName, transaction_field, transaction_part) {
      if (transaction_field == null) {
        transaction_field = '';
      }
      if (transaction_part == null) {
        transaction_part = '';
      }
      return "mapping[" + this.name + "][tdatafields][" + transaction_field + "][fields][" + fieldName + "]";
    };
    DimensionWidget.prototype.formFieldRequired = function(fieldName, fieldParent) {
      var _ref;
      if (fieldParent) {
        return ((_ref = FIELDS_META[fieldName]) != null ? _ref['required'] : void 0) || false;
      } else {
        return false;
      }
    };
    DimensionWidget.prototype.formFieldRequired2 = function(fieldName, fieldParent, transactionField) {
      var _ref, _ref2, _ref3, _ref4;
      if (transactionField) {
        if (fieldParent) {
          if (DEFAULT_FIELD_SETUP[fieldParent]) {
            if (DEFAULT_FIELD_SETUP[fieldParent]['tdatafields'][transactionField] && DEFAULT_FIELD_SETUP[fieldParent]['tdatafields'][transactionField]['fields'][fieldName]) {
              return ((_ref = DEFAULT_FIELD_SETUP[fieldParent]['tdatafields'][transactionField]['fields'][fieldName]) != null ? _ref['required'] : void 0) || false;
            } else {
              return false;
            }
          } else {
            return false;
          }
        } else {
          return ((_ref2 = FIELDS_META[fieldName]) != null ? _ref2['required'] : void 0) || false;
        }
      } else {
        if (fieldParent) {
          if (DEFAULT_FIELD_SETUP[fieldParent]) {
            if (DEFAULT_FIELD_SETUP[fieldParent]['fields'] && DEFAULT_FIELD_SETUP[fieldParent]['fields'][fieldName]) {
              return ((_ref3 = DEFAULT_FIELD_SETUP[fieldParent]['fields'][fieldName]) != null ? _ref3['required'] : void 0) || false;
            } else {
              return false;
            }
          } else {
            return false;
          }
        } else {
          return ((_ref4 = FIELDS_META[fieldName]) != null ? _ref4['required'] : void 0) || false;
        }
      }
    };
    DimensionWidget.prototype.onAddFieldClick = function(e) {
      var name, row;
      name = prompt("Field name:").trim();
      row = this._makeFieldRow(name);
      row.appendTo(this.element.find('tbody'));
      this.element.trigger('fillColumnsRequest', [row.find('select.column')]);
      return false;
    };
    DimensionWidget.prototype.onDeleteDimensionClick = function(e) {
      var theform;
      theform = this.element.parents('form').first();
      $(e.currentTarget).parents('fieldset').first().remove();
      theform.change();
      return false;
    };
    DimensionWidget.prototype.onDeleteTDataFieldClick = function(e) {
      var theform;
      theform = this.element.parents('form').first();
      $(e.currentTarget).parents('fieldset').first().remove();
      theform.change();
      return false;
    };
    DimensionWidget.prototype.onColumnChange = function(e) {
      var construct_iatifield, curDimension, dimension_data, dimension_name, thiscolumn;
      curDimension = $(e.currentTarget).parents('fieldset').first();
      dimension_name = curDimension.data('dimension-name');
      dimension_data = curDimension.serializeObject()['mapping'];
      thiscolumn = $(e.currentTarget).val();
      construct_iatifield = this.doIATIFieldSample(dimension_name, dimension_data, thiscolumn);
      curDimension.find('span').first().html('Sample data: <code></code>');
      curDimension.find('span code').first().text(construct_iatifield);
      this.element.parents('form').first().change();
      return false;
    };
    DimensionWidget.prototype.doIATIFieldSample = function(dimension_name, dimension_data, thiscolumn) {
      var construct_iatifield, k, samplevalue, textdata, v, _ref;
      construct_iatifield = '<' + dimension_data[dimension_name]['iati-field'];
      _ref = dimension_data[dimension_name]['fields'];
      for (k in _ref) {
        v = _ref[k];
        if (k === 'text') {
          if (v['datatype'] === 'constant') {
            textdata = dimension_data[dimension_name]['fields'][k]['constant'];
          } else {
            textdata = this.dataSample(dimension_data[dimension_name]['fields'][k]['column']);
          }
        } else {
          if (v['datatype'] === 'constant') {
            samplevalue = dimension_data[dimension_name]['fields'][k]['constant'];
          } else {
            samplevalue = this.dataSample(dimension_data[dimension_name]['fields'][k]['column']);
          }
          construct_iatifield = construct_iatifield + ' ' + k + '="' + samplevalue + '"';
        }
      }
      if (textdata) {
        construct_iatifield = construct_iatifield + ">" + textdata + "</" + dimension_data[dimension_name]['iati-field'] + ">";
      } else {
        construct_iatifield = construct_iatifield + "/>";
      }
      return construct_iatifield;
    };
    DimensionWidget.prototype.onIATIFieldChange = function(e) {
      var k, row, thisfield, thisfieldsfields, v;
      this.element.parents('form').first().change();
      thisfield = $(e.currentTarget).val();
      this.element.find('tbody tr').remove();
      thisfieldsfields = DEFAULT_FIELD_SETUP[thisfield]['fields'];
      for (k in thisfieldsfields) {
        v = thisfieldsfields[k];
        row = this._makeFieldRowUpdate(k, thisfield, v['required']);
        row.appendTo(this.element.find('tbody'));
        this.element.trigger('fillColumnsRequest', [row.find('select.column')]);
      }
      return false;
    };
    DimensionWidget.prototype.onFieldRemoveClick = function(e) {
      $(e.currentTarget).parents('tr').first().remove();
      this.element.parents('form').first().change();
      return false;
    };
    DimensionWidget.prototype.onFieldSwitchConstantClick = function(e) {
      var curDimension, curRow, iatiField, row;
      curRow = $(e.currentTarget).parents('tr').first();
      curDimension = $(e.currentTarget).parents('fieldset').first();
      iatiField = $(e.currentTarget).parents('fieldset').first().find('.iatifield').val();
      row = this._makeFieldRow(curRow.data('field-name'), curDimension.data('dimension-name'), iatiField, true);
      curRow.replaceWith(row);
      this.element.parents('form').first().change();
      return false;
    };
    DimensionWidget.prototype.onFieldSwitchColumnClick = function(e) {
      var curDimension, curRow, iatiField, row;
      curRow = $(e.currentTarget).parents('tr').first();
      curDimension = $(e.currentTarget).parents('fieldset').first();
      iatiField = $(e.currentTarget).parents('fieldset').first().find('.iatifield').val();
      row = this._makeFieldRow(curRow.data('field-name'), curDimension.data('dimension-name'), iatiField, false);
      curRow.replaceWith(row);
      this.element.trigger('fillColumnsRequest', [row.find('select.column')]);
      this.element.parents('form').first().change();
      return false;
    };
    DimensionWidget.prototype.onFieldSwitchConstantClickTransaction = function(e) {
      var curDimension, curDimensionPart, curRow, iatiField, newrow;
      curRow = $(e.currentTarget).parents('tr').first();
      curDimensionPart = $(e.currentTarget).parents('fieldset');
      curDimension = $(e.currentTarget).parents('fieldset').first();
      iatiField = $(e.currentTarget).parents('fieldset').first().find('.iatifield').val();
      newrow = this._makeFieldRowTransaction(curRow.data('field-name'), curDimensionPart.data('transaction-field-type'), curDimension.data('dimension-name'), iatiField, true);
      curRow.replaceWith(newrow);
      this.element.trigger('fillColumnsRequest', [newrow.find('select.column')]);
      this.element.parents('form').first().change();
      return false;
    };
    DimensionWidget.prototype.onFieldSwitchColumnClickTransaction = function(e) {
      var curDimension, curDimensionPart, curRow, iatiField, newrow;
      curRow = $(e.currentTarget).parents('tr').first();
      curDimensionPart = $(e.currentTarget).parents('fieldset');
      curDimension = $(e.currentTarget).parents('fieldset').first();
      iatiField = $(e.currentTarget).parents('fieldset').first().find('.iatifield').val();
      newrow = this._makeFieldRowTransaction(curRow.data('field-name'), curDimensionPart.data('transaction-field-type'), curDimension.data('dimension-name'), iatiField, false);
      curRow.replaceWith(newrow);
      this.element.trigger('fillColumnsRequest', [newrow.find('select.column')]);
      this.element.parents('form').first().change();
      return false;
    };
    DimensionWidget.prototype.promptAddDimensionNamed = function(props, thename) {
      return false;
    };
    DimensionWidget.prototype.dataSample = function(columnName) {
      return SAMPLE_DATA[columnName];
    };
    DimensionWidget.prototype._makeFieldRow = function(name, dimensionName, iatiField, constant) {
      var tplName;
      if (constant == null) {
        constant = false;
      }
      tplName = constant ? 'tpl_dimension_field_const' : 'tpl_dimension_field';
      return $.tmpl(tplName, {
        'fieldName': name,
        'dimensionName': dimensionName,
        'iatiField': iatiField,
        'prefix': this.formFieldPrefix,
        'required': this.formFieldRequired
      });
    };
    DimensionWidget.prototype._makeFieldRowTransaction = function(fieldname, transaction_field, dimension_name, iatiField, constant) {
      var tplName;
      if (constant == null) {
        constant = false;
      }
      tplName = constant ? 'tpl_dimension_field_const' : 'tpl_dimension_field';
      return $.tmpl(tplName, {
        'fieldName': fieldname,
        'transaction_field': transaction_field,
        'transaction_part': dimension_name,
        'prefix': this.formFieldTransactionPrefix,
        'required': this.formFieldRequired,
        'transaction': 'yes',
        'iatiField': iatiField
      });
    };
    DimensionWidget.prototype._makeFieldRowUpdate = function(name, thisfield, requiredvar, constant) {
      var tplName;
      if (constant == null) {
        constant = false;
      }
      tplName = constant ? 'tpl_dimension_field_const' : 'tpl_dimension_field';
      return $.tmpl(tplName, {
        'fieldName': name,
        'prefix': this.formFieldPrefix,
        'required': this.formFieldRequired2
      });
    };
    return DimensionWidget;
  })();
  DimensionsWidget = (function() {
    __extends(DimensionsWidget, Delegator);
    DimensionsWidget.prototype.events = {
      '.iati_field_add change': 'onAddIATIFieldClick',
      '.add_value_dimension click': 'onAddValueDimensionClick',
      '.add_compound_dimension click': 'onAddCompoundDimensionClick'
    };
    function DimensionsWidget(element, options) {
      DimensionsWidget.__super__.constructor.apply(this, arguments);
      this.widgets = [];
      this.dimsEl = this.element.find('.dimensions').get(0);
      this.element.trigger('doFieldSelectors', 'iatifield');
      this.element.trigger('doFieldSelectors', 'column');
    }
    DimensionsWidget.prototype.addDimension = function(name) {
      var w;
      w = new DimensionWidget(name, this.dimsEl);
      this.widgets.push(w);
      return w;
    };
    DimensionsWidget.prototype.removeDimension = function(name) {
      var idx, w, _i, _len, _ref;
      idx = null;
      _ref = this.widgets;
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        w = _ref[_i];
        if (w.name === name) {
          idx = this.widgets.indexOf(w);
          break;
        }
      }
      if (idx !== null) {
        return this.widgets.splice(idx, 1)[0].element.remove();
      }
    };
    DimensionsWidget.prototype.deserialize = function(data) {
      var dims, name, obj, toRemove, widget, _i, _j, _len, _len2, _ref, _results;
      if (this.ignoreParent) {
        return;
      }
      dims = data['mapping'] || {};
      toRemove = [];
      _ref = this.widgets;
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        widget = _ref[_i];
        if (widget.name in dims) {
          widget.deserialize(data);
          delete dims[widget.name];
        } else {
          toRemove.push(widget.name);
        }
      }
      for (_j = 0, _len2 = toRemove.length; _j < _len2; _j++) {
        name = toRemove[_j];
        this.removeDimension(name);
      }
      _results = [];
      for (name in dims) {
        obj = dims[name];
        _results.push(this.addDimension(name).deserialize(data));
      }
      return _results;
    };
    DimensionsWidget.prototype.promptAddDimension = function(props) {
      var data, iati_field, name;
      name = prompt("Give a unique name for your new dimension (letters and numbers, no spaces):");
      if (!name) {
        return false;
      }
      data = {
        'mapping': {}
      };
      data['mapping'][name] = props;
      iati_field = data['mapping'][name]['iati-field'];
      data['mapping'][name] = DEFAULT_FIELD_SETUP[iati_field];
      data['mapping'][name]['label'] = 'User field: ' + name;
      data['mapping'][name]['iati-field'] = iati_field;
      return this.addDimension(name.trim()).deserialize(data);
    };
    DimensionsWidget.prototype.promptAddDimensionNamed = function(thename, props) {
      var data, name;
      alert("Column \"" + thename + "\" has been added.");
      name = thename;
      if (!name) {
        return false;
      }
      data = {
        'mapping': {}
      };
      data['mapping'][name] = props;
      return this.addDimension(name.trim()).deserialize(data);
    };
    DimensionsWidget.prototype.onAddValueDimensionClick = function(e) {
      this.promptAddDimension({
        'datatype': 'value'
      });
      return false;
    };
    DimensionsWidget.prototype.onAddCompoundDimensionClick = function(e) {
      this.promptAddDimension({
        'datatype': 'compound'
      });
      return false;
    };
    DimensionsWidget.prototype.onAddIATIFieldClick = function(e) {
      var thefield;
      thefield = $(e.currentTarget).val();
      this.promptAddDimension({
        'datatype': 'compound',
        'iati-field': thefield
      });
      $(e.currentTarget).val('');
      return false;
    };
    return DimensionsWidget;
  })();
  ModelEditor = (function() {
    __extends(ModelEditor, Delegator);
    ModelEditor.prototype.widgetTypes = {
      '.unique_keys_widget': UniqueKeyWidget,
      '.dimensions_widget': DimensionsWidget
    };
    ModelEditor.prototype.events = {
      'multipleSectorsRequest': 'onMultipleSectorsSetup',
      'modelChange': 'onModelChange',
      'fillColumnsRequest': 'onFillColumnsRequest',
      'fillIATIfieldsRequest': 'onFillIATIfieldsRequest',
      '.steps > ul > li click': 'onStepClick',
      '.steps > ul > li > ul > li click': 'onStepDimensionClick',
      '.forms form submit': 'onFormSubmit',
      '.forms form change': 'onFormChange',
      '#showdebug click': 'onShowDebugClick',
      '.add_data_field click': 'onAddDataFieldClick',
      'doFieldSelectors': 'onDoFieldSelectors',
      '#columns .availablebtn click': 'onColumnsAvailableClick',
      '#columns .allbtn click': 'onColumnsAllClick',
      '#iatifields .availablebtn click': 'onIATIFieldsAvailableClick',
      '#iatifields .allbtn click': 'onIATIFieldsAllClick'
    };
    function ModelEditor(element, options) {
      var ctor, e, model_data, selector, x, _i, _len, _ref, _ref2;
      ModelEditor.__super__.constructor.apply(this, arguments);
      $('#multiple_rows_selector').html("<option value=''>One row per activity</option>" + ((function() {
        var _i, _len, _ref, _results;
        _ref = this.options.iatifields;
        _results = [];
        for (_i = 0, _len = _ref.length; _i < _len; _i++) {
          x = _ref[_i];
          if (x !== '') {
            _results.push("<option value='" + x + "'>Multiple " + x + " rows per activity</option>");
          }
        }
        return _results;
      }).call(this)).join('\n'));
      if (this.options.model_data) {
        model_data = JSON.parse(this.options.model_data);
      } else {
        model_data = DEFAULT_MODEL;
      }
      this.data = $.extend(true, {}, model_data);
      this.widgets = [];
      this.form = $(element).find('.forms form').eq(0);
      this.id = this.element.attr('id');
      if (!(this.id != null)) {
        this.id = Math.floor(Math.random() * 0xffffffff).toString(16);
        this.element.attr('id', this.id);
      }
      this.element.find('script[type="text/x-jquery-tmpl"]').each(function() {
        return $(this).template($(this).attr('id'));
      });
      this.options.columns.unshift('');
      this.element.find('select.iatifield').each(function() {
        return $(this).trigger('fillColumnsRequest', [this]);
      });
      this.options.iatifields.unshift('');
      this.element.find('select.iatifield').each(function() {
        return $(this).trigger('fillIATIfieldsRequest', [this]);
      });
      _ref = this.widgetTypes;
      for (selector in _ref) {
        ctor = _ref[selector];
        _ref2 = this.element.find(selector).get();
        for (_i = 0, _len = _ref2.length; _i < _len; _i++) {
          e = _ref2[_i];
          this.widgets.push(new ctor(e));
        }
      }
      this.element.trigger('modelChange');
      this.setStep(0);
    }
    ModelEditor.prototype.setStep = function(s) {
      $(this.element).find('.steps > ul > li').removeClass('active').eq(s).addClass('active');
      return $(this.element).find('.forms div.formpart').hide().eq(s).show();
    };
    ModelEditor.prototype.onStepClick = function(e) {
      var idx;
      idx = this.element.find('.steps > ul > li').index(e.currentTarget);
      this.setStep(idx);
      return false;
    };
    ModelEditor.prototype.onAddDataFieldClick = function(e) {
      var thevar, w, _i, _len, _ref;
      thevar = $(e.currentTarget).text();
      _ref = this.widgets;
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        w = _ref[_i];
        w.promptAddDimensionNamed(thevar, {
          'datatype': 'value',
          'column': thevar,
          'label': thevar
        });
      }
      this.data = this.form.serializeObject();
      this.element.trigger('modelChange');
      return $(e.currentTarget).removeClass('add_data_field available').addClass('unavailable');
    };
    ModelEditor.prototype.onShowDebugClick = function(e) {
      if ($('#debug').hasClass('debug-shown')) {
        $('#debug').slideUp().removeClass('debug-shown');
      } else {
        $('#debug').slideDown().addClass('debug-shown');
      }
      return false;
    };
    ModelEditor.prototype.onFormChange = function(e) {
      if (this.ignoreFormChange) {
        return;
      }
      this.data = this.form.serializeObject();
      this.form.find('.column').each(function() {
        var columnname;
        columnname = $(this).val();
        return $('#user_columns ul li a').each(function() {
          if (($(this).text()) === columnname) {
            return $(this).removeClass('available').addClass('unavailable');
          }
        });
      });
      this.element.trigger('doFieldSelectors', 'iatifield');
      this.element.trigger('doFieldSelectors', 'column');
      this.ignoreFormChange = true;
      this.element.trigger('modelChange');
      return this.ignoreFormChange = false;
    };
    ModelEditor.prototype.onColumnsAvailableClick = function(e) {
      $('#columns ul').addClass('hideunavailable');
      $('#columns .allbtn').removeClass('fieldsbuttons-selected');
      return $('#columns .availablebtn').addClass('fieldsbuttons-selected');
    };
    ModelEditor.prototype.onColumnsAllClick = function(e) {
      $('#columns ul').removeClass('hideunavailable');
      $('#columns .availablebtn').removeClass('fieldsbuttons-selected');
      return $('#columns .allbtn').addClass('fieldsbuttons-selected');
    };
    ModelEditor.prototype.onIATIFieldsAvailableClick = function(e) {
      $('#iatifields ul').addClass('hideunavailable');
      $('#iatifields .allbtn').removeClass('fieldsbuttons-selected');
      return $('#iatifields .availablebtn').addClass('fieldsbuttons-selected');
    };
    ModelEditor.prototype.onIATIFieldsAllClick = function(e) {
      $('#iatifields ul').removeClass('hideunavailable');
      $('#iatifields .availablebtn').removeClass('fieldsbuttons-selected');
      return $('#iatifields .allbtn').addClass('fieldsbuttons-selected');
    };
    ModelEditor.prototype.onDoFieldSelectors = function(e) {
      $('#' + e + 's ul li code').each(function() {
        if ($(this).hasClass('unavailable')) {
          $(this).removeClass('unavailable');
          return $(this).addClass('available');
        }
      });
      return this.form.find('.' + e).each(function() {
        var iatiname;
        iatiname = $(this).val();
        return $('#' + e + 's ul li code').each(function() {
          if ($(this).text() === iatiname) {
            $(this).removeClass('available');
            return $(this).addClass('unavailable');
          }
        });
      });
    };
    ModelEditor.prototype.onFormSubmit = function(e) {
      var api_address, csv_file, model_file;
      e.preventDefault();
      api_address = 'api_convert';
      model_file = $('#convert_model_file_URL').val();
      csv_file = $('#convert_csv_file_URL').val();
      $.post(api_address, {
        csv_file: csv_file,
        model_file: model_file
      }, {
        complete: function(result) {
          return alert(result.status);
        }
      }, "json");
      return false;
    };
    ModelEditor.prototype.onModelChange = function() {
      var dimNames, k, n, v, w, _i, _len, _ref, _ref2;
      _ref = util.flattenObject(this.data);
      for (k in _ref) {
        v = _ref[k];
        this.form.find("[name=\"" + k + "\"]").val(v);
      }
      _ref2 = this.widgets;
      for (_i = 0, _len = _ref2.length; _i < _len; _i++) {
        w = _ref2[_i];
        w.deserialize($.extend(true, {}, this.data));
      }
      dimNames = (function() {
        var _ref3, _results;
        _ref3 = this.data['mapping'];
        _results = [];
        for (k in _ref3) {
          v = _ref3[k];
          _results.push(k);
        }
        return _results;
      }).call(this);
      this.element.find('.steps ul.steps_dimensions').html(((function() {
        var _j, _len2, _results;
        _results = [];
        for (_j = 0, _len2 = dimNames.length; _j < _len2; _j++) {
          n = dimNames[_j];
          _results.push('<li><a href="#' + ("m1_dim_" + n) + '">' + ("" + this.data['mapping'][n]['label'] + "</a>"));
        }
        return _results;
      }).call(this)).join('\n'));
      return $('#debug').text(JSON.stringify(this.data, null, 2));
    };
    ModelEditor.prototype.onFillColumnsRequest = function(elem) {
      var x;
      return $(elem).html(((function() {
        var _i, _len, _ref, _results;
        _ref = this.options.columns;
        _results = [];
        for (_i = 0, _len = _ref.length; _i < _len; _i++) {
          x = _ref[_i];
          _results.push("<option value='" + x + "'>" + x + "</option>");
        }
        return _results;
      }).call(this)).join('\n'));
    };
    ModelEditor.prototype.onFillIATIfieldsRequest = function(elem) {
      var x;
      return $(elem).html(((function() {
        var _i, _len, _ref, _results;
        _ref = this.options.iatifields;
        _results = [];
        for (_i = 0, _len = _ref.length; _i < _len; _i++) {
          x = _ref[_i];
          _results.push("<option value='" + x + "'>" + x + "</option>");
        }
        return _results;
      }).call(this)).join('\n'));
    };
    return ModelEditor;
  })();
  $.plugin('modelEditor', ModelEditor);
  this.ModelEditor = ModelEditor;
}).call(this);
