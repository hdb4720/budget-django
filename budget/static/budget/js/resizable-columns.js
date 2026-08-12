// budget/static/budget/js/resizable-columns.js

(function () {
    function makeTableResizable(table) {
        const ths = table.querySelectorAll("thead th");
        if (!ths.length) return;

        // Ensure table uses fixed layout for predictable resizing
        table.style.tableLayout = "fixed";

        ths.forEach((th) => {
            // Create grip element
            const grip = document.createElement("div");
            grip.className = "rc-grip";
            grip.style.position = "absolute";
            grip.style.top = "0";
            grip.style.right = "0";
            grip.style.width = "6px";
            grip.style.cursor = "col-resize";
            grip.style.userSelect = "none";
            grip.style.height = "100%";

            // Make header position relative so grip can sit inside
            th.style.position = "relative";

            th.appendChild(grip);

            let startX;
            let startWidth;

            function onMouseDown(e) {
                e.preventDefault();
                startX = e.pageX;
                startWidth = th.offsetWidth;

                document.addEventListener("mousemove", onMouseMove);
                document.addEventListener("mouseup", onMouseUp);
            }

            function onMouseMove(e) {
                const delta = e.pageX - startX;
                const newWidth = Math.max(40, startWidth + delta); // minimum width
                th.style.width = newWidth + "px";

                // Apply width to corresponding column cells
                const index = Array.prototype.indexOf.call(th.parentNode.children, th);
                table.querySelectorAll("tbody tr").forEach((row) => {
                    const cell = row.children[index];
                    if (cell) {
                        cell.style.width = newWidth + "px";
                    }
                });
            }

            function onMouseUp() {
                document.removeEventListener("mousemove", onMouseMove);
                document.removeEventListener("mouseup", onMouseUp);
            }

            grip.addEventListener("mousedown", onMouseDown);
        });
    }

    // Initialize on all .report-table elements
    function initResizableTables() {
        document.querySelectorAll(".report-table").forEach(makeTableResizable);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initResizableTables);
    } else {
        initResizableTables();
    }
})();
