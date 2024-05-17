// Clips all inputs to their min/max values.
// Returns true iff any input was changed.
function validateInputs() {
    let changed = false;
    $("input").each(function() {
        switch ($(this).attr('type')) {
            case 'checkbox':
                let is_checked = $(this).attr('checked');
                $(this).val(is_checked);
                return;
            case 'number':
                let originalVal = parseInt($(this).val());
                let maxVal = parseInt($(this).attr('max'));
                let minVal = parseInt($(this).attr('min'));
                if (isNaN(originalVal)) {
                    let defaultVal = parseInt($(this).prop('defaultValue'));
                    $(this).val(defaultVal);
                    changed = true;
                } else if (originalVal > maxVal) {
                    $(this).val(maxVal);
                    changed = true;
                } else if (originalVal < minVal) {
                    $(this).val(minVal);
                    changed = true;
                }
        }
    });
    
    return changed;
}

function inputsAreValid() {
    let allValid = true;
    $("input").each(function() {
        if ($(this).attr('type') != 'number') {
            return;
        }
        let val = parseInt($(this).val());
        let maxVal = parseInt($(this).attr('max'));
        let minVal = parseInt($(this).attr('min'));
        if (isNaN(val) || val > maxVal || val < minVal) {
            allValid = false;
        }
    });
    return allValid;
}

// Sets inputs based on search query by id (assumed to be equal to name).
function setInputsFromSearchQuery() {
    let searchParams = new URLSearchParams(window.location.search);
    searchParams.forEach(function(value, key) {
        let field = $("#" + key);
        if (field.attr('type') == 'checkbox') {
            field.attr('checked', true);
        } else if (field.attr('type') == 'number') {
            let n = parseInt(value);
            if (!(n >= field.attr('min') && n <= field.attr('max'))) {
                return;
            }
        }
        field.val(value);
    });
}

// Updates search query based on all forms.
function updateSearchQueryFromForms() {
    let searchParams = $("form").serialize();
    history.replaceState(null, "", "?" + searchParams);
}
