document.addEventListener('DOMContentLoaded', function() {
    console.log('email_cron_job.js loaded');

    // Initialize Flatpickr for cron_time with AM/PM
    const cronTimeInput = document.getElementById('id_cron_time');
    if (cronTimeInput) {
        console.log('Initializing Flatpickr for cron_time');
        flatpickr(cronTimeInput, {
            enableTime: true,
            noCalendar: true,
            dateFormat: "H:i:S",  // Changed to 24-hour format for consistent parsing
            time_24hr: true,      // Use 24-hour format for input
            onChange: function(selectedDates, dateStr, instance) {
                console.log('cron_time changed:', dateStr);
                // Store the time in 24-hour format (UTC)
                cronTimeInput.value = dateStr;
                console.log('Time set to:', dateStr);
            }
        });

        // Convert UTC time to local time for editing
        if (cronTimeInput.value) {
            try {
                console.log('Converting UTC time to local for cron_time:', cronTimeInput.value);
                const timeValue = cronTimeInput.value;

                // Make sure we're working with a valid time string
                let timeParts;
                if (timeValue.includes(' ')) {
                    // Handle format like "1:00:00 PM"
                    const [timePortion, period] = timeValue.split(' ');
                    timeParts = timePortion.split(':').map(Number);
                    if (period === 'PM' && timeParts[0] < 12) {
                        timeParts[0] += 12;
                    } else if (period === 'AM' && timeParts[0] === 12) {
                        timeParts[0] = 0;
                    }
                } else {
                    // Handle format like "13:00:00"
                    timeParts = timeValue.split(':').map(Number);
                }

                // Ensure we have valid parts
                if (timeParts.length >= 2) {
                    const hours = timeParts[0].toString().padStart(2, '0');
                    const minutes = timeParts[1].toString().padStart(2, '0');
                    const seconds = (timeParts[2] || 0).toString().padStart(2, '0');

                    // Set in 24-hour format for Flatpickr
                    const formattedTime = `${hours}:${minutes}:${seconds}`;
                    console.log('Displaying formatted time:', formattedTime);
                    cronTimeInput._flatpickr.setDate(formattedTime, true);
                }
            } catch (error) {
                console.error('Error parsing time:', error);
            }
        }
    } else {
        console.error('Cron time input (#id_cron_time) not found');
    }

    // Handle frequency change to show/hide end_date
    const frequencySelect = document.getElementById('id_frequency');
    console.log('Found frequency select:', frequencySelect);

    // Get the end_date field container
    const endDateField = document.querySelector('.form-group.field-end_date');
    console.log('Found end date field using .form-group.field-end_date:', endDateField);

    function toggleEndDate() {
        if (!frequencySelect || !endDateField) {
            console.error('Required elements not found', {
                frequencySelect: Boolean(frequencySelect),
                endDateField: Boolean(endDateField)
            });
            return;
        }

        const currentValue = frequencySelect.value;
        console.log('Toggling end_date visibility, current frequency:', currentValue);

        if (currentValue === 'specific_date') {
            console.log('Hiding end date field');
            endDateField.style.display = 'none';

            const endDateInput = document.getElementById('id_end_date');
            if (endDateInput) {
                endDateInput.value = '';
                console.log('Cleared end_date input value');
            }
        } else {
            console.log('Showing end date field');
            endDateField.style.display = '';  // Use empty string instead of 'block' to restore default display
        }
    }

    // Initialize select2 if available (for better UX)
    if (window.$ && $.fn.select2 && frequencySelect) {
        $(frequencySelect).on('select2:select', function() {
            console.log('select2 change detected');
            toggleEndDate();
        });
    }

    // Initial toggle and event listener
    if (frequencySelect && endDateField) {
        console.log('Setting up frequency change handling');

        // Initial toggle
        toggleEndDate();

        // Standard event listener for changes
        frequencySelect.addEventListener('change', function() {
            console.log('Frequency changed to:', this.value);
            toggleEndDate();
        });
    }

    // Initialize Flatpickr for date fields
    const startDateInput = document.getElementById('id_start_date');
    if (startDateInput) {
        console.log('Initializing Flatpickr for start_date');
        flatpickr(startDateInput, {
            dateFormat: "Y-m-d",
        });
    } else {
        console.error('Start date input (#id_start_date) not found');
    }

    const endDateInput = document.getElementById('id_end_date');
    if (endDateInput) {
        console.log('Initializing Flatpickr for end_date');
        flatpickr(endDateInput, {
            dateFormat: "Y-m-d",
        });
    } else {
        console.error('End date input (#id_end_date) not found');
    }

    // Additional helper to ensure toggleEndDate runs after Django's tab initialization
    if (typeof window.addEventListener === 'function') {
        window.addEventListener('notify', function(e) {
            if (e.detail === 'init_tab') {
                console.log('Tab initialized, re-running toggleEndDate');
                setTimeout(toggleEndDate, 100);
            }
        });
    }
});