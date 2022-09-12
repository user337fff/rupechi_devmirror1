if (!$) {
    $ = django.jQuery;
}

(function() {
    'use strict'

    var addBtn = document.querySelector('.select-btn-control')
    var dropdown = {
        element: addBtn.parentElement.querySelector('.select-btn-dropdown'),
        opened: false,

        open() {
            this.element.style.display = 'block'
            this.opened = true
        },

        close() {
            this.element.style.display = 'none'
            this.opened = false
        }
    }

    // Обработчик дропдауна
    addBtn.onclick = function(event) {
        event.preventDefault()
        if (dropdown.opened) {
            dropdown.close()
        } else {
            dropdown.open()
        }
    }


    /////////////////////////////////////////
    // Drag and Drop и сортировка инлайнов //
    /////////////////////////////////////////

    //Иницилизация drag and drop Dragula
    var container = document.querySelector(".inlinesets-container")
    var drake = dragula([container])

    initSort()
    drake.on('dragend', reindexSortFields)

    function reindexSortFields(element = null) {
        // Иницилизация закрывашки
        if (element !== null) initRollUp(element)

        var inlinesHTML = container.querySelectorAll('.inline-item')

        inlinesHTML.forEach(function(inline, index) {
            var sort = inline.querySelector('.field-sort input')
            sort.value = index
        })
        

        // Fix для CKEDITOR
        if (element !== null) {
            var textarea = element.querySelector('textarea[data-type=ckeditortype]')
            if (textarea !== null) {
                var instance = CKEDITOR.instances[textarea.id]
                if (instance !== undefined) {
                    element.style.height = element.clientHeight + 2 + 'px'
                    instance.destroy(true)
                    // textarea.nextElementSibling.remove()
                    textarea.dataset.processed = "0"
                    document.dispatchEvent(new Event('DOMContentLoaded'))
                    setTimeout(function() {
                        element.style.height = ''
                    }, 100)
                }
            }
        }
    }

    function initSort() {
        function compareSort(inlineA, inlineB) {
            return inlineA.sort - inlineB.sort;
        }

        var inlinesHTML = container.querySelectorAll('.inline-item')
        var inlines = new Array()

        inlinesHTML.forEach(function(inline, index) {
            inlines.push({
                inline: inline,
                sort: parseInt(inline.querySelector('.field-sort input').value)
            })
        })

        inlines.sort(compareSort)

        inlines.forEach(function(item) {
            container.appendChild(item.inline)
        })
    }


    ///////////////////////////
    // Сворачивание инлайнов //
    ///////////////////////////

    Array.prototype.slice.call(container.children).forEach(initRollUp)

    function initRollUp(inline) {
        var btn = inline.querySelector('.inline-item-roll-up')
        var body = inline.querySelector('.inline-item-body')

        btn.onclick = function(event) {
            if (btn.classList.contains('active')) {
                btn.classList.remove('active')
                body.style.display = ''
                document.dispatchEvent(new Event('DOMContentLoaded'))
            } else {
                btn.classList.add('active')
                body.style.display = 'none'
            }
        }
    }


    //////////////////////////////////////
    // Кастомные инлайны моделей Django //
    //////////////////////////////////////

    var CustomInlines = (function() {
        var defaults = {
            prefix: "form",
            addText: "add another",
            deleteText: "remove",
            deleteCssClass: "inline-item-remove",
            emptyCssClass: "inline-item-empty",
            formCssClass: "inline-item-dynamic",
        }

        function CustomInlines(item, options) {
            this.options = {
                prefix:             options.prefix || defaults.prefix,
                addText:            options.addText || defaults.addText,
                deleteText:         options.deleteText || defaults.deleteText,
                deleteCssClass:     options.deleteCssClass || defaults.deleteCssClass,
                emptyCssClass:      options.emptyCssClass || defaults.emptyCssClass,
                formCssClass:       options.formCssClass || defaults.formCssClass ,
            }
            this.container = document.querySelector('.inlinesets-container')
            this.data = document.querySelector('.inlines-data')
            this.template = item.querySelector('#' + this.options.prefix + '-empty')
            this.totalForms = this.data.querySelector('#id_' + options.prefix + '-TOTAL_FORMS')
            this.maxForms = this.data.querySelector('#id_' + options.prefix + '-MAX_NUM_FORMS')
            this.nextIndex = parseInt(this.totalForms.value, 10)
            this.showAddButton = this.maxForms.value === '' || (this.maxForms.value - this.totalForms.value) > 0

            // Autocomplete off для скрытых полей с данными
            this.totalForms.autocomplete = 'off'
            this.maxForms.autocomplete = 'off'

            item.onclick = this.add.bind(this)
        }

        CustomInlines.prototype = {
            add(event) {
                var _this = this
                event.preventDefault()

                var row = this.template.cloneNode(this)
                var deleteBtn = parseHTML('<a class="' + this.options.deleteCssClass + '" href="#">' + this.options.deleteText + "</a>")

                // Формируем инлайн элемент модели
                row.classList.remove(this.options.emptyCssClass)
                row.classList.add(this.options.formCssClass)
                row.id = this.options.prefix + '-' + this.nextIndex
                row.querySelector('.inline-item-actions').appendChild(deleteBtn)
                $(row).find('*').each(function(i, element) {
                    _this.updateElementIndex(element, _this.options.prefix, _this.totalForms.value)
                })

                // Вывод инлайна на страницу
                this.container.appendChild(row)

                // Обновление индекса
                this.totalForms.value = parseInt(this.totalForms.value, 10) + 1
                this.nextIndex++

                this.reinitDateTimeShortCuts()
                this.updateSelectFilter()
                this.initPrepopulatedFields(row)
                reindexSortFields()
                initRollUp(row)

                // Тригерим окончание загрузки содержимого страницы для
                // иницилизации CKEditor'а
                document.dispatchEvent(new Event('DOMContentLoaded'))

                window.dispatchEvent(new Event('resize'))

                // Закрытие дропдауна
                dropdown.close()

                // Обработчик удаления инлайна
                deleteBtn.onclick = function(event) {
                    event.preventDefault()

                    console.log('remmove')
                    // Удаление
                    row.remove()
                    _this.nextIndex--

                    // Переиндексация всех инлайнов той же модели
                    var forms = _this.container.querySelectorAll(".inline-item-" + _this.options.prefix)
                    _this.totalForms.value = forms.length
                    forms.forEach(function(item, index) {
                        _this.updateElementIndex(item, _this.options.prefix, index)
                        $(item).find('*').each(function(ind, element) {
                            _this.updateElementIndex(element, _this.options.prefix, index)
                        })
                    })

                    reindexSortFields()
                }
            },

            updateElementIndex(element, prefix, index) {
                var id_regex = new RegExp("(" + prefix + "-(\\d+|__prefix__))")
                var replacement = prefix + "-" + index
                if (element.for !== undefined) {
                    element.for = element.for.replace(id_regex, replacement)
                }
                if (element.id !== undefined) {
                    element.id = element.id.replace(id_regex, replacement)
                }
                if (element.name !== undefined) {
                    element.name = element.name.replace(id_regex, replacement)
                }
            },

            initPrepopulatedFields(row) {
                row.querySelectorAll('.prepopulated_field').forEach(function(item) {
                    var field = $(item),
                        input = field.find('input, select, textarea'),
                        dependency_list = input.data('dependency_list') || [],
                        dependencies = []
                    $.each(dependency_list, function (i, field_name) {
                        dependencies.push('#' + $(row).find('.field-' + field_name).find('input, select, textarea').attr('id'))
                    });
                    if (dependencies.length) {
                        input.prepopulate(dependencies, input.attr('maxlength'))
                    }
                })
            },

            reinitDateTimeShortCuts() {
                if (typeof DateTimeShortcuts !== "undefined") {
                    $(".datetimeshortcuts").remove();
                    DateTimeShortcuts.init();
                }
            },

            updateSelectFilter() {
                if (typeof SelectFilter !== 'undefined') {
                    $('.selectfilter').each(function(index, value) {
                        var namearr = value.name.split('-');
                        SelectFilter.init(value.id, namearr[namearr.length - 1], false);
                    });
                    $('.selectfilterstacked').each(function(index, value) {
                        var namearr = value.name.split('-');
                        SelectFilter.init(value.id, namearr[namearr.length - 1], true);
                    });
                }
            }
        }

        return CustomInlines
    }())

    Array.prototype.slice.call(dropdown.element.children).forEach(function(item) {
        var options = JSON.parse(item.dataset.inlineFormset).options
        new CustomInlines(item, options)
    })
})()