class FormState {
    constructor(formElement) {
        this.formElement = formElement;
        this.invalidFields = [];
        this.errorMessages = {};
    }

    addInvalidField(field, message) {
        if (!this.invalidFields.includes(field)) {
            this.invalidFields.push(field);
            this.errorMessages[field] = message;
        }
    }

    removeInvalidField(field) {
        this.invalidFields = this.invalidFields.filter(item => item !== field);
        delete this.errorMessages[field];
    }

    updateErrorDisplay() {
        const errorPlace = document.getElementById("error_place");
        if (this.invalidFields.length > 0) {
            errorPlace.innerHTML = `<p class="error_msge">Please fill out: ${this.invalidFields.join(", ")}</p>`;
        } else {
            errorPlace.innerHTML = ""; // Clear error messages
        }
    }

    isFormValid() {
        return this.invalidFields.length === 0;
    }
}

document.addEventListener("DOMContentLoaded", function () {
    const formElement = document.getElementById("testForm");
    const formState = new FormState(formElement);

    formElement.addEventListener("submit", function (event) {
        validateForm(event, formState, "Please fill out");
    });

    attachDynamicErrorRemoval(formState);
});

function validateForm(event, formState, message) {
    const inputs = formState.formElement.querySelectorAll("input");
    formState.invalidFields = [];
    formState.errorMessages = {};

    inputs.forEach((input) => {
        if (input.value.trim() === "") {
            formState.addInvalidField(input.placeholder, `${message} (${input.placeholder})`);
            input.style.borderWidth = "5px";
            input.style.borderColor = "#f8d7da";
            input.style.color = "#842029";
        } else {
            input.style.border = "";
            input.style.color = "";
        }
    });

    formState.updateErrorDisplay();

    if (!formState.isFormValid()) {
        event.preventDefault();
    }
}

function attachDynamicErrorRemoval(formState) {
    const inputs = formState.formElement.querySelectorAll("input");

    inputs.forEach((input) => {
        input.addEventListener("input", () => {
            if (input.value.trim() !== "") {
                formState.removeInvalidField(input.placeholder);
                formState.updateErrorDisplay();
                input.style.border = "";
                input.style.color = "";
            }
        });
    });
}

// Function: Set up dynamic descriptions for goals
function setupDynamicDescriptions() {
    const choices = document.getElementById("choices");
    if (choices) {
        choices.addEventListener("change", function () {
            const descriptionText = document.getElementById("descriptionText");
            const selectedOption = choices.options[choices.selectedIndex];

            if (selectedOption) {
                descriptionText.textContent = selectedOption.dataset.description || "";
            }

            if (choices.value === "custom") {
                let container = document.getElementById("custom-inputs");
                container.innerHTML = `
                    <input type="text" name="name" placeholder="Enter your goal"><br>
                    <input type="number" name="target_amount" placeholder="Enter amount of money"><br>
                    <input type="number" name="term" placeholder="Enter the goal term">
                    <select name="time">
                        <option value="year">Year</option>
                        <option value="month">Month</option>
                        <option value="week">Week</option>
                        <option value="day">Day</option>
                    </select>`;
            } else {
                document.getElementById("custom-inputs").innerHTML = "";
            }
        });
    }
}




//I made these to show description
function showDescriptionbutton(id, descriptionId, button) {
    let descriptionElement = document.getElementById(descriptionId);
     if (descriptionElement.innerText) {
         descriptionElement.innerText = "";
         button.style.backgroundColor = "blue";
     } else {
         let description = document.getElementById(id).getAttribute("data-description");
         descriptionElement.innerText = description;
         button.style.backgroundColor = "rgb(100, 100, 100)";
}
}


// show description for select
function showDescription() {
    var select = document.getElementById("choices");
    var selectedOption = select.options[select.selectedIndex];
    var description = selectedOption.getAttribute("data-description");
    document.getElementById("descriptionText").innerText = description;
}
document.getElementById("choices").addEventListener("change", function() {
    if (this.value === "custom") {
        let container = document.getElementById("custom-inputs-goals");
        container.innerHTML = '<input type="text" name="name" placeholder="Enter your goal"><br>' +
                              '<input type="number" name="target_amount" placeholder="Enter amount of money"><br>' +
                              '<input type="number" name="term" placeholder="Enter the goal term">' +
                              '<select name="time">' +
                                  '<option value="year">year</option>' +
                                  '<option value="month">month</option>' +
                                  '<option value="week">week</option>' +
                                  '<option value="day">day</option>' +
                              '</select>';
    } else {
        let container = document.getElementById("custom-inputs-goals");
        container.innerHTML = '';
     }
});


addSpentForm.addEventListener('submit', function (e) {
    e.preventDefault();

    const formData = new FormData(addSpentForm);

    // Validate inputs
    if (!formData.get('category') || !formData.get('amount')) {
        alert('Please fill out all fields.');
        return;
    }

    fetch('/add_spent', {
        method: 'POST',
        body: formData,
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            alert(data.message || 'Added successfully!');

            // Update the table dynamically
            const category = formData.get('category');
            const amount = parseFloat(formData.get('amount'));

            const row = Array.from(document.querySelectorAll('#budgetTableBody tr')).find(
                row => row.cells[0].textContent === category
            );

            if (row) {
                const spentCell = row.cells[2];
                const remainingCell = row.cells[3];

                const currentSpent = parseFloat(spentCell.textContent.replace('$', ''));
                const currentRemaining = parseFloat(remainingCell.textContent.replace('$', ''));

                spentCell.textContent = `$${(currentSpent + amount).toFixed(2)}`;
                remainingCell.textContent = `$${(currentRemaining - amount).toFixed(2)}`;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to add spent amount. Please try again.');
        });
});





