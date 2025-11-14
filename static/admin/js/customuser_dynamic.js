console.log("✅ customuser_dynamic.js loaded successfully");

// Run after admin form loads
document.addEventListener("DOMContentLoaded", function () {
    const stateSelect = document.getElementById("id_states");
    const districtSelect = document.getElementById("id_districts");
    const officeSelect = document.getElementById("id_offices");

    if (!stateSelect || !districtSelect || !officeSelect) {
        console.warn("⚠️ CustomUser admin: some fields missing.");
        return;
    }

    // Helper: Clear + repopulate dropdown
    function populateSelect(select, data) {
        select.innerHTML = "";
        data.forEach((item) => {
            const opt = document.createElement("option");
            opt.value = item.id;
            opt.textContent = item.name;
            select.appendChild(opt);
        });
    }

    // Helper: Get selected IDs from admin multiselect box
    function getSelectedIds(selectBoxId) {       console.warn("⚠️ CustomUser admin: some fields missing.");
        const box = document.querySelector(`#${selectBoxId} option:checked`);
        const selected = Array.from(document.querySelectorAll(`#${selectBoxId}_to option`)).map(opt => opt.value);
        return selected.join(",");
    }

    // 🔄 Function: Refresh districts when states change
    function refreshDistricts() {
        const stateIds = getSelectedIds("id_states");
        console.log("Selected States:", stateIds);
        if (!stateIds) {
            districtSelect.innerHTML = "";
            officeSelect.innerHTML = "";
            return;
        }

        fetch(`/admin/account/customuser/ajax/get-districts/?state_ids=${stateIds}`)
            .then(r => r.json())
            .then(data => {
                console.log("Fetched Districts:", data);
                populateSelect(districtSelect, data);
                officeSelect.innerHTML = "";
            })
            .catch(e => console.error("❌ Error loading districts:", e));
    }

    // 🔄 Function: Refresh offices when districts change
    function refreshOffices() {
        const districtIds = getSelectedIds("id_districts");
        console.log("Selected Districts:", districtIds);
        if (!districtIds) {
            officeSelect.innerHTML = "";
            return;
        }

        fetch(`/admin/account/customuser/ajax/get-offices/?district_ids=${districtIds}`)
            .then(r => r.json())
            .then(data => {
                console.log("Fetched Offices:", data);
                populateSelect(officeSelect, data);
            })
            .catch(e => console.error("❌ Error loading offices:", e));
    }

    // 🧠 Important: Use Django admin’s “SelectFilter” event listener
    document.body.addEventListener("change", function (e) {
        if (e.target.closest("#id_states")) {
            refreshDistricts();
        } else if (e.target.closest("#id_districts")) {
            refreshOffices();
        }
    });

    // Also handle “Add →” / “Remove ←” buttons
    document.body.addEventListener("click", function (e) {
        if (e.target.closest("a.selector-add") || e.target.closest("a.selector-remove")) {
            setTimeout(() => {
                refreshDistricts();
                refreshOffices();
            }, 500);
        }
    });
});
