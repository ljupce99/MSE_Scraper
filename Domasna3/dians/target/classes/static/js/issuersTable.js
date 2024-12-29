
var jsonPath = "/download/names.json";

window.onload = function () {
    fetch(jsonPath)
        .then(function (response) {

            if (!response.ok) {
                throw new Error("" + response.statusText);
            }
            return response.json();
        })
        .then(function (jsonData) {
            if (!Array.isArray(jsonData)) {
                document.getElementById("tableContainer").innerHTML =
                    "<p style='color: red;'>JSON must be an array of objects!</p>";
                return;
            }

            // Clear existing content
            var tableContainer = document.getElementById("tableContainer");
            tableContainer.innerHTML = "";

            // Create the table
            var table = document.createElement("table");
            var thead = document.createElement("thead");
            var tbody = document.createElement("tbody");

            // Generate table headers (from the first object's keys)
            var headers = Object.keys(jsonData[0]);
            var headerRow = document.createElement("tr");
            headers.forEach(function (header) {
                var th = document.createElement("th");
                th.textContent = header;
                headerRow.appendChild(th);
            });
            thead.appendChild(headerRow);

            // Generate table rows
            jsonData.forEach(function (item) {
                var row = document.createElement("tr");
                headers.forEach(function (header) {
                    var cell = document.createElement("td");
                    cell.textContent = item[header] || "";
                    row.appendChild(cell);
                });
                tbody.appendChild(row);
            });

            table.appendChild(thead);
            table.appendChild(tbody);
            tableContainer.appendChild(table);
        })
        .catch(function (error) {
            document.getElementById("tableContainer").innerHTML =
                "<p style='color: red;'>" + error.message + "</p>";
        });
};