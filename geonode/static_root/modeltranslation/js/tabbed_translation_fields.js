/*jslint white: true, onevar: true, undef: true, nomen: true, eqeqeq: true,
  plusplus: true, bitwise: true, regexp: true, newcap: true, immed: true */
var google, django, gettext;

(function () {
    var jQuery = window.jQuery || $ || django.jQuery;

    /* Add a new selector to jQuery that excludes parent items which match a given selector */
    jQuery.expr[':'].parents = function(a, i, m) {
        return jQuery(a).parents(m[3]).length < 1;
    };

    jQuery(function ($) {
        var TranslationField = function (options) {
            this.el = options.el;
            this.cls = options.cls;
            this.id = '';
            this.origFieldname = '';
            this.lang = '';
            this.groupId = '';

            this.init = function () {
                var clsBits = this.cls.substring(
                    TranslationField.cssPrefix.length, this.cls.length).split('-');
                this.origFieldname = clsBits[0];
                this.lang = clsBits[1];
                this.id = $(this.el).attr('id');
                this.groupId = this.buildGroupId();
            };

            this.buildGroupId = function () {
                /**
                 * Returns a unique group identifier with respect to the admin's way
                 * of handling inline field name attributes. Essentially that's the
                 * translation field id without the language prefix.
                 *
                 * Examples ('id parameter': 'return value'):
                 *
                 *  'id_name_de':
                 *      'id_name'
                 *  'id_name_zh_tw':
                 *      'id_name'
                 *  'id_name_set-2-name_de':
                 *      'id_name_set-2-name'
                 *  'id_name_set-2-name_zh_tw':
                 *      'id_name_set-2-name'
                 *  'id_name_set-2-0-name_de':
                 *      'id_name_set-2-0-name'
                 *  'id_name_set-2-0-name_zh_tw':
                 *      'id_name_set-2-0-name'
                 *  'id_news-data2-content_type-object_id-0-name_de':
                 *      'id_news-data2-content_type-object_id-0-name'
                 *  'id_news-data2-content_type-object_id-0-name_zh_cn':
                 *      id_news-data2-content_type-object_id-0-name'
                 *  'id_news-data2-content_type-object_id-0-1-name_de':
                 *      'id_news-data2-content_type-object_id-0-1-name'
                 *  'id_news-data2-content_type-object_id-0-1-name_zh_cn':
                 *      id_news-data2-content_type-object_id-0-1-name'
                 */
                // TODO: We should be able to simplify this, the modeltranslation specific
                // field classes are already build to be easily splitable, so we could use them
                // to slice off the language code.
                var idBits = this.id.split('-'),
                    idPrefix = 'id_' + this.origFieldname;
                if (idBits.length === 3) {
                    // Handle standard inlines
                    idPrefix = idBits[0] + '-' + idBits[1] + '-' + idPrefix;
                } else if (idBits.length === 4) {
                    // Handle standard inlines with model used by inline more than once
                    idPrefix = idBits[0] + '-' + idBits[1] + '-' + idBits[2] + '-' + idPrefix;
                } else if (idBits.length === 5 && idBits[3] != '__prefix__') {
                    // Handle nested inlines (https://github.com/Soaa-/django-nested-inlines)
                    idPrefix = idBits[0] + '-' + idBits[1] + '-' + idBits[2] + '-' + idBits[3] + '-' + this.origFieldname;
                } else if (idBits.length === 6) {
                    // Handle generic inlines
                    idPrefix = idBits[0] + '-' + idBits[1] + '-' + idBits[2] + '-' +
                        idBits[3] + '-' + idBits[4] + '-' + this.origFieldname;
                } else if (idBits.length === 7) {
                    // Handle generic inlines with model used by inline more than once
                    idPrefix = idBits[0] + '-' + idBits[1] + '-' + idBits[2] + '-' +
                        idBits[3] + '-' + idBits[4] + '-' + idBits[5] + '-' + this.origFieldname;
                }
                return idPrefix;
            };

            this.init();
        };
        TranslationField.cssPrefix = 'mt-field-';

        var TranslationFieldGrouper = function (options) {
            this.$fields = options.$fields;
            this.groupedTranslations = {};

            this.init = function () {
                // Handle fields inside collapsed groups as added by zinnia
                this.$fields = this.$fields.add('fieldset.collapse-closed .mt');

                this.groupedTranslations = this.getGroupedTranslations();
            };

            this.getGroupedTranslations = function () {
                /**
                 * Returns a grouped set of all model translation fields.
                 * The returned datastructure will look something like this:
                 *
                 * {
                 *     'id_name_de': {
                 *         'en': HTMLInputElement,
                 *         'de': HTMLInputElement,
                 *         'zh_tw': HTMLInputElement
                 *     },
                 *     'id_name_set-2-name': {
                 *         'en': HTMLTextAreaElement,
                 *         'de': HTMLTextAreaElement,
                 *         'zh_tw': HTMLTextAreaElement
                 *     },
                 *     'id_news-data2-content_type-object_id-0-name': {
                 *         'en': HTMLTextAreaElement,
                 *         'de': HTMLTextAreaElement,
                 *         'zh_tw': HTMLTextAreaElement
                 *     }
                 * }
                 *
                 * The keys are unique group identifiers as returned by
                 * TranslationField.buildGroupId() to handle inlines properly.
                 */
                var self = this,
                    cssPrefix = TranslationField.cssPrefix;
                this.$fields.each(function (idx, el) {
                    $.each($(el).attr('class').split(' '), function(idx, cls) {
                        if (cls.substring(0, cssPrefix.length) === cssPrefix) {
                            var tfield = new TranslationField({el: el, cls: cls});
                            if (!self.groupedTranslations[tfield.groupId]) {
                                self.groupedTranslations[tfield.groupId] = {};
                            }
                            self.groupedTranslations[tfield.groupId][tfield.lang] = el;
                        }
                    });
                });
                return this.groupedTranslations;
            };

            this.init();
        };

        function createTabs(groupedTranslations) {
            var tabs = [];
            $.each(groupedTranslations, function (groupId, lang) {
                var tabsContainer = $('<div></div>'),
                    tabsList = $('<ul></ul>'),
                    insertionPoint;
                tabsContainer.append(tabsList);
                $.each(lang, function (lang, el) {
                    var container = $(el).closest('.form-row'),
                        label = $('label', container),
                        fieldLabel = container.find('label'),
                        tabId = 'tab_' + $(el).attr('id'),
                        panel,
                        tab;
                    // Remove language and brackets from field label, they are
                    // displayed in the tab already.
                    if (fieldLabel.html()) {
                        fieldLabel.html(fieldLabel.html().replace(/ \[.+\]/, ''));
                    }
                    if (!insertionPoint) {
                        insertionPoint = {
                            'insert': container.prev().length ? 'after' :
                                container.next().length ? 'prepend' : 'append',
                            'el': container.prev().length ? container.prev() : container.parent()
                        };
                    }
                    container.find('script').remove();
                    panel = $('<div id="' + tabId + '"></div>').append(container);
                    tab = $('<li' + (label.hasClass('required') ? ' class="required"' : '') +
                            '><a href="#' + tabId + '">' + lang.replace('_', '-') + '</a></li>');
                    tabsList.append(tab);
                    tabsContainer.append(panel);
                });
                insertionPoint.el[insertionPoint.insert](tabsContainer);
                tabsContainer.tabs();
                tabs.push(tabsContainer);
            });
            return tabs;
        }

        function handleAddAnotherInline() {
            // TODO: Refactor
            $('.mt').parents('.inline-group').not('.tabular').find('.add-row a').click(function () {
                var grouper = new TranslationFieldGrouper({
                    $fields: $(this).parent().prev().prev().find('.mt')
                });
                var tabs = createTabs(grouper.groupedTranslations);
                // Update the main switch as it is not aware of the newly created tabs
                MainSwitch.update(tabs);
                // Activate the language tab selected in the main switch
                MainSwitch.activateTab(tabs);
            });
        }

        var TabularInlineGroup = function (options) {
            this.id = options.id;
            this.$id = null;
            this.$table = null;
            this.translationColumns = [];
            // TODO: Make use of this to flag required tabs
            this.requiredColumns = [];

            this.init = function () {
                this.$id = $('#' + this.id);
                this.$table = $(this.$id).find('table');
            };

            this.getAllGroupedTranslations = function () {
                var grouper = new TranslationFieldGrouper({
                    $fields: this.$table.find('.mt').filter(
                        'input:visible, textarea:visible, select:visible')
                });
                //this.requiredColumns = this.getRequiredColumns();
                this.initTable();
                return grouper.groupedTranslations;
            };

            this.getGroupedTranslations = function ($fields) {
                var grouper = new TranslationFieldGrouper({
                    $fields: $fields
                });
                return grouper.groupedTranslations;
            };

            this.initTable = function () {
                var self = this;
                // The table header requires special treatment. In case an inline
                // is declared with extra=0, the translation fields are not visible.
                var thGrouper = new TranslationFieldGrouper({
                    $fields: this.$table.find('.mt').filter('input, textarea, select')
                });
                this.translationColumns = this.getTranslationColumns(thGrouper.groupedTranslations);

                // The markup of tabular inlines is kinda weird. There is an additional
                // leading td.original per row, so we have one td more than ths.
                this.$table.find('th').each(function (idx) {
                    // Hide table heads from which translation fields have been moved out.
                    if($.inArray(idx + 1, self.translationColumns) !== -1) {
                        // FIXME: Why does this break when we use remove instead of hide?
                        $(this).hide();
                    }

                    // Remove language and brackets from table header,
                    // they are displayed in the tab already.
                    if ($(this).html() && $.inArray(idx + 1, self.translationColumns) === -1) {
                        $(this).html($(this).html().replace(/ \[.+\]/, ''));
                    }
                });
            };

            this.getTranslationColumns = function (groupedTranslations) {
                var translationColumns = [];
                // Get table column indexes which have translation fields, but omit the first
                // one per group, because that's where we insert our tab container.
                $.each(groupedTranslations, function (groupId, lang) {
                    var i = 0;
                    $.each(lang, function (lang, el) {
                        var column = $(el).closest('td').prevAll().length;
                        if (i > 0 && $.inArray(column, translationColumns) === -1) {
                            translationColumns.push(column);
                        }
                        i += 1;
                    });
                });
                return translationColumns;
            };

            this.getRequiredColumns = function () {
                var requiredColumns = [];
                // Get table column indexes which have required fields, but omit the first
                // one per group, because that's where we insert our tab container.
                this.$table.find('th.required').each(function () {
                    requiredColumns.push($(this).index() + 1);
                });
                return requiredColumns;
            };

            this.init();
        };

        function handleTabularAddAnotherInline(tabularInlineGroup) {
            tabularInlineGroup.$table.find('.add-row a').click(function () {
                var tabs = createTabularTabs(
                    tabularInlineGroup.getGroupedTranslations(
                        $(this).parent().parent().prev().prev().find('.mt')));
                // Update the main switch as it is not aware of the newly created tabs
                MainSwitch.update(tabs);
                // Activate the language tab selected in the main switch
                MainSwitch.activateTab(tabs);
            });
        }

        function createTabularTabs(groupedTranslations) {
            var tabs = [];

            $.each(groupedTranslations, function (groupId, lang) {
                var tabsContainer = $('<td></td>'),
                    tabsList = $('<ul></ul>'),
                    insertionPoint;
                tabsContainer.append(tabsList);

                $.each(lang, function (lang, el) {
                    var $container = $(el).closest('td'),
                        $panel,
                        $tab,
                        tabId = 'tab_' + $(el).attr('id');
                    if (!insertionPoint) {
                        insertionPoint = {
                            'insert': $container.prev().length ? 'after' :
                                $container.next().length ? 'prepend' : 'append',
                            'el': $container.prev().length ? $container.prev() : $container.parent()
                        };
                    }
                    $panel = $('<div id="' + tabId + '"></div>').append($container);

                    // Turn the moved tds into divs
                    var attrs = {};
                    $.each($container[0].attributes, function(idx, attr) {
                        attrs[attr.nodeName] = attr.nodeValue;
                    });
                    $container.replaceWith(function () {
                        return $('<div />', attrs).append($(this).contents());
                    });

                    // TODO: Setting the required state based on the default field is naive.
                    // The user might have tweaked his admin. We somehow have to keep track of the
                    // column indexes _before_ the tds have been moved around.
                    $tab = $('<li' + ($(el).hasClass('mt-default') ? ' class="required"' : '') +
                             '><a href="#' + tabId + '">' + lang.replace('_', '-') + '</a></li>');
                    tabsList.append($tab);
                    tabsContainer.append($panel);
                });
                insertionPoint.el[insertionPoint.insert](tabsContainer);
                tabsContainer.tabs();
                tabs.push(tabsContainer);
            });
            return tabs;
        }

        var MainSwitch = {
            languages: [],
            $select: $('<select>'),

            init: function(groupedTranslations, tabs) {
                var self = this;
                $.each(groupedTranslations, function (id, languages) {
                    $.each(languages, function (lang) {
                        if ($.inArray(lang, self.languages) < 0) {
                            self.languages.push(lang);
                        }
                    });
                });
                $.each(this.languages, function (idx, language) {
                    self.$select.append($('<option value="' + idx + '">' +
                                        language.replace('_', '-') + '</option>'));
                });
                this.update(tabs);
                $('#content').find('h1').append('&nbsp;').append(self.$select);
            },

            update: function(tabs) {
                var self = this;
                this.$select.change(function () {
                    $.each(tabs, function (idx, tab) {
                        try { //jquery ui => 1.10 api changed, we keep backward compatibility
                            tab.tabs('select', parseInt(self.$select.val(), 10));
                        } catch(e) {
                            tab.tabs('option', 'active', parseInt(self.$select.val(), 10));
                        }
                    });
                });
            },

            activateTab: function(tabs) {
                var self = this;
                $.each(tabs, function (idx, tab) {
                    try { //jquery ui => 1.10 api changed, we keep backward compatibility
                        tab.tabs('select', parseInt(self.$select.val(), 10));
                    } catch(e) {
                        tab.tabs('option', 'active', parseInt(self.$select.val(), 10));
                    }
                });
            }
        };

        if ($('body').hasClass('change-form')) {
            // Group normal fields and fields in (existing) stacked inlines
            var grouper = new TranslationFieldGrouper({
                $fields: $('.mt').filter(
                    'input:visible, textarea:visible, select:visible, iframe').filter(':parents(.tabular)')
            });
            MainSwitch.init(grouper.groupedTranslations, createTabs(grouper.groupedTranslations));

            // Note: The add another functionality in admin is injected through inline javascript,
            // here we have to run after that (and after all other ready events just to be sure).
            $(document).ready(function() {
                $(window).load(function() {
                    handleAddAnotherInline();
                });
            });

            // Group fields in (existing) tabular inlines
            $('div.inline-group > div.tabular').each(function () {
                var tabularInlineGroup = new TabularInlineGroup({
                    'id': $(this).parent().attr('id')
                });
                MainSwitch.update(
                    createTabularTabs(tabularInlineGroup.getAllGroupedTranslations()));

                $(document).ready(function() {
                    $(window).load(function() {
                        handleTabularAddAnotherInline(tabularInlineGroup);
                    });
                });
            });
        }
    });
}());
