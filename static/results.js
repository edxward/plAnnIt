document.addEventListener("DOMContentLoaded", () => {
    document.getElementById('button1').click();
});

function loadTableFromFile(filename, clickedButton = null) {
    fetch(filename)
      .then(response => response.json())
      .then(jsonData => {
        const scheduleContainer = document.getElementById('schedule');
        scheduleContainer.innerHTML = '';

        document.querySelectorAll('.button').forEach(button => button.classList.remove('active'));
        if (clickedButton) clickedButton.classList.add('active');

        const schedule = jsonData[0];
        const burnout_score_raw = jsonData[1];

        for (let day in schedule) {
          if (schedule.hasOwnProperty(day)) {
            const dayHeading = document.createElement('h3');
            dayHeading.textContent = day;
            scheduleContainer.appendChild(dayHeading);

            const table = document.createElement('table');

            const thead = document.createElement('thead');
            const headerRow = document.createElement('tr');
            ['Task', 'Start Time', 'End Time'].forEach(text => {
              const th = document.createElement('th');
              th.textContent = text;
              headerRow.appendChild(th);
            });
            thead.appendChild(headerRow);
            table.appendChild(thead);

            const tbody = document.createElement('tbody');

            schedule[day].forEach(taskObj => {
              const taskName = Object.keys(taskObj)[0];
              const times = taskObj[taskName];

              const row = document.createElement('tr');

              const tdTask = document.createElement('td');
              tdTask.textContent = taskName;
              row.appendChild(tdTask);

              const tdStart = document.createElement('td');
              tdStart.textContent = times[0];
              row.appendChild(tdStart);

              const tdEnd = document.createElement('td');
              tdEnd.textContent = times[1];
              row.appendChild(tdEnd);

              tbody.appendChild(row);
            });

            table.appendChild(tbody);
            scheduleContainer.appendChild(table);
          }
        }
        const burnoutHTML = document.createElement('h2');
        burnoutHTML.textContent = "Burnout Score: " + burnout_score_raw;
        scheduleContainer.appendChild(burnoutHTML);
      })
      .catch(error => console.error('Error loading JSON:', error));
}


function getCsv(timetableNumber) {
    a = window.location.pathname.slice(-1)
    b = timetableNumber
    window.location.href = `/csv_convert?json=${a}_${b}`;
    
}