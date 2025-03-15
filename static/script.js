let ecaCount = 0;
let otherCount = 0;

function addECA(name = "", type = "", start = "", finish = "", stress = "", date = "") {
    const container = document.getElementById("ecaContainer");
    const index = ecaCount++;

    const ecaDiv = document.createElement("div");
    ecaDiv.classList.add("form-group");
    ecaDiv.id = `eca${index}`;

    ecaDiv.innerHTML = `
        <div class="school-timings-section">
            <div class="form-group">
                <label>ECA Name:</label>
                <input type="text" id="ecaName${index}" value="${name}">
            </div>
            <div></div>
            <div class="form-group">
                <label>Type:</label>
                <input type="text" id="ecaType${index}" value="${type}">
            </div>
        </div>
        <div class="school-timings-section">
            <div class="form-group">
                <label>Start Time:</label>
                <input type="time" id="ecaStart${index}" value="${start}">
            </div>
            <div></div>
            <div class="form-group">
                <label>Finish Time:</label>
                <input type="time" id="ecaFinish${index}" value="${finish}">
            </div>
        </div>
        <div class="school-timings-section">
            <div class="form-group">
                <label>Days:</label>
                <select id="ecaDate${index}" name="options" multiple>
                  <option value="Monday">Monday</option>
                  <option value="Tuesday">Tuesday</option>
                  <option value="Wednesday">Wednesday</option>
                  <option value="Thursday">Thursday</option>
                  <option value="Friday">Friday</option>
                  <option value="Saturday">Saturday</option>
                  <option value="Sunday">Sunday</option>
                </select>
            </div>
            <div></div>
            <div class="form-group">
                <label>Stressfulness (1-10):</label>
                <input type="number" id="ecaStress${index}" value="${stress}" min="1" max="10">
            </div>
        </div>
        <button type="button" class="remove-btn" onclick="removeElement('eca${index}')">Remove</button>
    `;

    container.appendChild(ecaDiv);

    const newSelect = document.getElementById(`ecaDate${index}`);
    new Choices(newSelect, {
        removeItemButton: true,
        placeholder: true,
        searchEnabled: false,
        shouldSort: false
    });
}

function addOtherActivity(name = "", type = "", duration = "", stress = "", date = "") {
    const container = document.getElementById("otherActivitiesContainer");
    const index = otherCount++;

    const otherDiv = document.createElement("div");
    otherDiv.classList.add("form-group");
    otherDiv.id = `other${index}`;

    otherDiv.innerHTML = `
        <div class="school-timings-section">
            <div class="form-group">
                <label>Activity Name:</label>
                <input type="text" id="otherName${index}" value="${name}">
            </div>
            <div></div>
            <div class="form-group">
                <label>Type:</label>
                <input type="text" id="otherType${index}" value="${type}">
            </div>
        </div>
        <div class="school-timings-section">
            <div class="form-group">
                <label>Estimated Duration (minutes):</label>
                <input type="number" id="otherDuration${index}" value="${duration}" min="1">
            </div>
            <div></div>
            <div class="form-group">
                <label>Stressfulness (1-10):</label>
                <input type="number" id="otherStress${index}" value="${stress}" min="1" max="10">
            </div>
        </div>
        <button type="button" class="remove-btn" onclick="removeElement('other${index}')">Remove</button>
    `;

    container.appendChild(otherDiv);
}


function removeElement(id) {
    const element = document.getElementById(id);
    if (element) {
        element.remove();
    } else {
        console.error("Element not found:", id);
    }
}

function submitForm() {
    document.getElementById('submitButton').textContent = "Generating Timetable ...";
    const data = {
        school_timetable: {
            monday_to_thursday: {
                start_time: document.getElementById("monThuStart").value,
                finish_time: document.getElementById("monThuFinish").value
            },
            friday: {
                start_time: document.getElementById("friStart").value,
                finish_time: document.getElementById("friFinish").value
            }
        },
        ecas: [],
        other_activities: []
    };

    // Process each ECA block
    document.querySelectorAll(".form-group[id^='eca']").forEach((ecaDiv) => {
        const index = ecaDiv.id.replace("eca", "");
        const name = document.getElementById(`ecaName${index}`).value;
        const type = document.getElementById(`ecaType${index}`).value;
        const start_time = document.getElementById(`ecaStart${index}`).value;
        const finish_time = document.getElementById(`ecaFinish${index}`).value;
        const stressfulness = parseInt(document.getElementById(`ecaStress${index}`).value) || 0;
        
        // Get all selected days
        const dateSelect = document.getElementById(`ecaDate${index}`);
        const selectedDays = Array.from(dateSelect.selectedOptions).map(option => option.value);
        
        // For each selected day, create a separate ECA entry
        selectedDays.forEach((day, counter) => {
            const uniqueName = selectedDays.length > 1 ? `${name} ${counter + 1}` : name;
            data.ecas.push({
                name: uniqueName,
                type,
                start_time,
                finish_time,
                date: day,
                stressfulness
            });
        });
    });

    document.querySelectorAll(".form-group[id^='other']").forEach((otherDiv) => {
        const index = otherDiv.id.replace("other", "");
        data.other_activities.push({
            name: document.getElementById(`otherName${index}`).value,
            type: document.getElementById(`otherType${index}`).value,
            duration: parseInt(document.getElementById(`otherDuration${index}`).value) || 0,
            stressfulness: parseInt(document.getElementById(`otherStress${index}`).value) || 0
        });
    });

    console.log("Form Data: ", JSON.stringify(data, null, 2));

    fetch("/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => document.location.href = "/timetable/" + data)
    .catch(error => console.error("Error:", error));
}