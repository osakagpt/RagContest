document.getElementById('contestForm').addEventListener('submit', function (event) {
    event.preventDefault();

    const formData = new FormData(this);
    const data = {
        contest_info: {
            "name": formData.get('contest_name'), 
            "description": formData.get('contest_description')},
        data_sources: [],
        query_answers: []
    };

    // Gather data sources
    const urlElements = document.querySelectorAll('.data-source-group .url');
    const typeElements = document.querySelectorAll('.data-source-group .data_type');
    const descriptionElements = document.querySelectorAll('.data-source-group .description');
    urlElements.forEach((urlElement, index) => {
        const dataSource = {
            path: urlElement.value,
            type: typeElements[index].value,
            description: descriptionElements[index].value
        };
        data.data_sources.push(dataSource);
    });

    // Gather query answers
    const queryElements = document.querySelectorAll('.query-answer-group .query');
    const numberOfOptionsElements = document.querySelectorAll('.query-answer-group .number-of-options');
    const optionsContainers = document.querySelectorAll('.query-answer-group .options');
    const queryDescriptionElements = document.querySelectorAll('.query-answer-group .description');

    queryElements.forEach((queryElement, index) => {
        const queryAnswer = {
            query: queryElement.value,
            options: [],
            answer: '',
            description: queryDescriptionElements[index].value
        };
        const numberOfOptions = parseInt(numberOfOptionsElements[index].value, 10);

        if (numberOfOptions > 0) {
            const optionInputs = optionsContainers[index].querySelectorAll('input.option');
            optionInputs.forEach(optionInput => {
                queryAnswer.options.push(optionInput.value);
            });
            const answerSelect = queryElement.parentElement.querySelector('.answer');
            queryAnswer.answer = answerSelect.value;
        } else {
            const answerInput = queryElement.parentElement.querySelector('.answer');
            queryAnswer.answer = answerInput.value;
        }

        data.query_answers.push(queryAnswer);
    });

    // Send data using Fetch API
    console.log(data);
    fetch('/register_contest', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    }).then(response => response.json())
        .then(data => console.log(data))
        .catch(error => console.error('Error:', error));
});


function generateOptions(select) {
    const numberOfOptions = parseInt(select.value, 10);
    const optionsContainer = select.nextElementSibling;
    const answerInput = select.parentElement.querySelector('.answer');
    if (numberOfOptions === 0) {
        // Delete the labels and options
        // Remove label and input elements
        while (optionsContainer.firstChild) {
            optionsContainer.removeChild(optionsContainer.firstChild);
        }

        // Reset answer input to text input
        if (answerInput.tagName.toLowerCase() === 'select') {
            const newTextInput = document.createElement('input');
            newTextInput.type = 'text';
            newTextInput.className = 'answer';
            newTextInput.name = answerInput.name;
            answerInput.replaceWith(newTextInput);
        }
    } else {
        // Reset options and change answer input to select box
        optionsContainer.innerHTML = ''; // Clear existing options
        const answerSelect = document.createElement('select');
        answerSelect.className = 'answer';
        answerSelect.name = answerInput.name;
        for (let i = 0; i < numberOfOptions; i++) {
            const optionLabel = document.createElement('label');
            optionLabel.textContent = `Option ${i + 1}:`;
            const optionInput = document.createElement('input');
            optionInput.type = 'text';
            optionInput.className = 'option';
            optionInput.name = `option${select.name.split('[')[1]}`;
            optionInput.oninput = function () {
                updateAnswerOptions(answerSelect, optionsContainer);
            };
            optionsContainer.appendChild(optionLabel);
            optionsContainer.appendChild(optionInput);
            optionsContainer.appendChild(document.createElement('br'));
        }
        answerInput.replaceWith(answerSelect);
        updateAnswerOptions(answerSelect, optionsContainer);
    }
}

function updateAnswerOptions(answerSelect, optionsContainer) {
    answerSelect.innerHTML = ''; // Clear existing options in answer select box
    optionsContainer.querySelectorAll('input.option').forEach((optionInput, index) => {
        const option = document.createElement('option');
        option.value = optionInput.value;
        option.textContent = `Option ${index + 1}: ${optionInput.value}`;
        answerSelect.appendChild(option);
    });
}

function addDataSourceSection() {
    const dataSourceGroup = document.querySelector('.data-source-group').cloneNode(true);
    dataSourceGroup.querySelectorAll('input').forEach(input => input.value = '');
    document.getElementById('data_source').appendChild(dataSourceGroup);
}

function removeDataSourceSection() {
    const dataSourceGroups = document.querySelectorAll('.data-source-group');
    if (dataSourceGroups.length > 1) {
        dataSourceGroups[dataSourceGroups.length - 1].remove();
    }
}


function addQueryAnswerSection() {
    const queryAnswerGroup = document.querySelector('.query-answer-group').cloneNode(true);
    queryAnswerGroup.querySelectorAll('input').forEach(input => input.value = '');
    queryAnswerGroup.querySelectorAll('.options').forEach(div => div.innerHTML = '');

    // Set number of options to 0
    const numberOfOptionsInput = queryAnswerGroup.querySelector('.number-of-options');
    numberOfOptionsInput.value = '0';

    // Change answer input to textbox
    const answerInput = queryAnswerGroup.querySelector('.answer');
    const newTextInput = document.createElement('input');
    newTextInput.type = 'text';
    newTextInput.className = 'answer';
    newTextInput.name = answerInput.name;
    answerInput.replaceWith(newTextInput);

    document.getElementById('query_answer').appendChild(queryAnswerGroup);
}


function removeQueryAnswerSection() {
    const queryAnswerGroups = document.querySelectorAll('.query-answer-group');
    if (queryAnswerGroups.length > 1) {
        queryAnswerGroups[queryAnswerGroups.length - 1].remove();
    }
}
