document.addEventListener('DOMContentLoaded', function() {
    console.log("Tasks Admin JS loaded.");

    function toggleEndDateFields() {
        // Get the selected radio button for end_date_choice
        var modeRadio = document.querySelector('input[name="end_date_choice"]:checked');
        if (!modeRadio) {
            console.log("No end_date_choice radio selected.");
            return;
        }
        var mode = modeRadio.value;
        console.log("Selected mode:", mode);

        // Use the container class from your HTML markup:
        var manualRow = document.querySelector('div.form-group.field-manual_end_date');
        var periodValueRow = document.querySelector('div.form-group.field-period_value');
        var periodUnitRow = document.querySelector('div.form-group.field-period_unit');

        if (mode === 'manual') {
            if (manualRow) {
                manualRow.style.display = ''; // show manual end date field
                console.log("Manual end date field displayed.");
            }
            if (periodValueRow) {
                periodValueRow.style.display = 'none'; // hide period fields
                console.log("Period value field hidden.");
            }
            if (periodUnitRow) {
                periodUnitRow.style.display = 'none';
                console.log("Period unit field hidden.");
            }
        } else if (mode === 'period') {
            if (manualRow) {
                manualRow.style.display = 'none'; // hide manual end date field
                console.log("Manual end date field hidden.");
            }
            if (periodValueRow) {
                periodValueRow.style.display = ''; // show period fields
                console.log("Period value field displayed.");
            }
            if (periodUnitRow) {
                periodUnitRow.style.display = '';
                console.log("Period unit field displayed.");
            }
        }
    }

    // Bind change event to the radio buttons for end_date_choice.
    var radios = document.querySelectorAll('input[name="end_date_choice"]');
    radios.forEach(function(radio) {
        radio.addEventListener('change', function() {
            console.log("Radio button changed:", radio.value);
            toggleEndDateFields();
        });
    });

    // Initialize the form with the correct fields visible.
    toggleEndDateFields();
});
