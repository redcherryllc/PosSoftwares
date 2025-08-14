  function updateBranches() {
            const unitSelect = document.getElementById('business_unit');
            const branchSelect = document.getElementById('branch');
            const selectedUnitId = unitSelect.value;

            branchSelect.innerHTML = '<option value="">Select Branch</option>';

            if (selectedUnitId) {
                fetch(`/get_branches/?business_unit_id=${selectedUnitId}`)
                    .then(response => response.json())
                    .then(data => {
                        data.forEach(branch => {
                            const option = document.createElement('option');
                            option.value = branch.branch_id;
                            option.text = branch.branch_name;
                            branchSelect.appendChild(option);
                        });
                    });
            }
        }