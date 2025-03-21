CKEDITOR.plugins.add('placeholders', {
    icons: 'placeholders',
    init: function(editor) {
        // Add the main Placeholders button with a dropdown
        editor.ui.addButton('Placeholders', {
            label: 'Placeholders',
            command: 'showPlaceholders',
            toolbar: 'insert',
            icon: this.path + 'icons/placeholders.png',
            hasArrow: true
        });

        // Add the command to show the dropdown
        editor.addCommand('showPlaceholders', {
            exec: function(editor) {
                // Create a menu for the dropdown
                var menu = new CKEDITOR.menu(editor, {
                    callback: function(key) {
                        if (key === 'create') {
                            openCreateDialog(editor);
                        } else if (key === 'default') {
                            openDefaultDialog(editor);
                        }
                    }
                });

                menu.addItem({
                    label: 'Create Placeholder',
                    command: 'create',
                    group: 'placeholders'
                });

                menu.addItem({
                    label: 'Default Placeholders',
                    command: 'default',
                    group: 'placeholders'
                });

                menu.show(editor.container.getWindow().getDocument().getById(editor.toolbar._.items[0]._.id));
            }
        });

        // Function to open the create dialog
        function openCreateDialog(editor) {
            editor.openDialog('placeholderCreateDialog');
        }

        // Function to open the default placeholders dialog
        function openDefaultDialog(editor) {
            editor.openDialog('placeholderSelectDialog');
        }

        // Dialog for creating new placeholders
        CKEDITOR.dialog.add('placeholderCreateDialog', function(editor) {
            return {
                title: 'Create New Placeholder',
                minWidth: 400,
                minHeight: 200,
                contents: [
                    {
                        id: 'tab1',
                        label: 'Settings',
                        elements: [
                            {
                                type: 'text',
                                id: 'key',
                                label: 'Display Name',
                                validate: CKEDITOR.dialog.validate.notEmpty("Name cannot be empty.")
                            },
                            {
                                type: 'text',
                                id: 'value',
                                label: 'Placeholder Value',
                                setup: function() {
                                    this.getDialog().getContentElement('tab1', 'key').on('keyup', function() {
                                        var key = this.getValue().toLowerCase().replace(/ /g, '_');
                                        var valueField = this.getDialog().getContentElement('tab1', 'value');
                                        valueField.setValue('{' + key + '}');
                                    });
                                },
                                validate: CKEDITOR.dialog.validate.notEmpty("Value cannot be empty.")
                            }
                        ]
                    }
                ],
                onOk: function() {
                    var key = this.getValueOf('tab1', 'key');
                    var value = this.getValueOf('tab1', 'value');
                    fetch('pep/placeholders/create/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': window.CSRF_TOKEN
                        },
                        body: JSON.stringify({ key: key, value: value })
                    }).then(response => {
                        if (response.ok) {
                            editor.insertText(value);
                        } else {
                            alert('Error saving placeholder.');
                        }
                    });
                }
            };
        });

        // Dialog for selecting default placeholders
        CKEDITOR.dialog.add('placeholderSelectDialog', function(editor) {
            return {
                title: 'Insert Placeholder',
                minWidth: 300,
                minHeight: 100,
                contents: [{
                    id: 'tab1',
                    label: 'Placeholders',
                    elements: [{
                        type: 'select',
                        id: 'placeholder',
                        label: 'Select a placeholder',
                        items: [],
                        setup: function() {
                            var select = this;
                            fetch('pep/placeholders/json/')
                                .then(response => response.json())
                                .then(data => {
                                    var items = data.map(ph => [ph.key, ph.value]);
                                    select.items = items;
                                    var element = select.getInputElement().$;
                                    element.innerHTML = items.map(ph => `<option value="${ph[1]}">${ph[0]}</option>`).join('');
                                });
                        }
                    }]
                }],
                onOk: function() {
                    var value = this.getValueOf('tab1', 'placeholder');
                    editor.insertText(value);
                }
            };
        });
    }
});