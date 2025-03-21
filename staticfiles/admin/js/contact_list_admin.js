document.addEventListener('DOMContentLoaded', function() {
    console.log("contact_list_admin.js loaded");

    // Function to show/hide fields based on the selected method
    function toggleFields() {
        var methodElem = document.querySelector('input[name="import_or_manual"]:checked');
        if (!methodElem) {
            console.log("No radio button is selected.");
            return;
        }
        var method = methodElem.value;
        console.log("Selected method:", method);

        // Use .form-group selectors as per your HTML structure.
        var excelFieldRow = document.querySelector('.form-group.field-excel_file');
        var contactsFieldRow = document.querySelector('.form-group.field-contacts_new');

        console.log("excelFieldRow element:", excelFieldRow);
        console.log("contactsFieldRow element:", contactsFieldRow);

        if (method === 'import') {
            if (excelFieldRow) {
                excelFieldRow.style.display = 'block';
                console.log("Showing Excel file field.");
            }
            if (contactsFieldRow) {
                contactsFieldRow.style.display = 'none';
                console.log("Hiding contacts field.");
            }
        } else {
            if (excelFieldRow) {
                excelFieldRow.style.display = 'none';
                console.log("Hiding Excel file field.");
            }
            if (contactsFieldRow) {
                contactsFieldRow.style.display = 'block';
                console.log("Showing contacts field.");
            }
        }
    }

    // Attach change event listeners to radio inputs
    var radios = document.querySelectorAll('input[name="import_or_manual"]');
    radios.forEach(function(radio) {
        radio.addEventListener('change', toggleFields);
        console.log("Attached event to radio:", radio);
    });

    // Initial toggle on page load
    toggleFields();

    // Add loading spinner functionality
    const form = document.getElementById('contactlist_form'); // Ensure this matches your form's ID
    if (form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault(); // Prevent default form submission

            // Create the loading spinner container
            const spinnerContainer = document.createElement('div');
            spinnerContainer.id = 'loading-spinner-container';
            spinnerContainer.style.position = 'fixed';
            spinnerContainer.style.top = '0';
            spinnerContainer.style.left = '0';
            spinnerContainer.style.width = '100%';
            spinnerContainer.style.height = '100%';
            spinnerContainer.style.backgroundColor = 'rgba(255, 255, 255, 0.8)';
            spinnerContainer.style.zIndex = '1000';
            spinnerContainer.style.display = 'flex';
            spinnerContainer.style.justifyContent = 'center';
            spinnerContainer.style.alignItems = 'center';

            // Create the spinner animation
            const spinner = document.createElement('div');
            spinner.style.border = '4px solid #f3f3f3';
            spinner.style.borderTop = '4px solid #3498db';
            spinner.style.borderRadius = '50%';
            spinner.style.width = '40px';
            spinner.style.height = '40px';
            spinner.style.animation = 'spin 1s linear infinite';

            // Add the spinner to the container
            spinnerContainer.appendChild(spinner);

            // Add the container to the body
            document.body.appendChild(spinnerContainer);

            // Disable the submit button to prevent multiple submissions
            const submitButton = form.querySelector('input[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
            }

            // Add CSS for the spinner animation
            const style = document.createElement('style');
            style.innerHTML = `
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            `;
            document.head.appendChild(style);

            // Submit the form via AJAX
            const formData = new FormData(form);
            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest', // Indicate AJAX request
                },
            })
                .then(response => response.json())
                .then(data => {
                    // Handle the response
                    if (data.success) {
//                        alert(data.message);
                        if (data.redirect_url) {
                            window.location.href = data.redirect_url; // Redirect to the contact list page
                        }
                    } else {
                        alert('Error: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while processing the form.');
                })
                .finally(() => {
                    // Remove the spinner and re-enable the submit button
                    spinnerContainer.remove();
                    if (submitButton) {
                        submitButton.disabled = false;
                    }
                });
        });
    }
});