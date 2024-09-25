// Search for Customer Table
function searchCustomerTable() {
  let input = document.getElementById("searchCustomerInput").value.toLowerCase();
  let table = document.getElementById("userTable");
  let tr = table.getElementsByTagName("tr");

  for (let i = 1; i < tr.length; i++) {
    let td = tr[i].getElementsByTagName("td")[0];
    if (td) {
      let txtValue = td.textContent || td.innerText;
      tr[i].style.display = txtValue.toLowerCase().indexOf(input) > -1 ? "" : "none";
    }
  }
}

// Search for NGO Table
function searchNgoTable() {
  let input = document.getElementById("searchNgoInput").value.toLowerCase();
  let table = document.getElementById("ngoInfoTable");
  let tr = table.getElementsByTagName("tr");

  for (let i = 1; i < tr.length; i++) {
    let td = tr[i].getElementsByTagName("td")[0];
    if (td) {
      let txtValue = td.textContent || td.innerText;
      tr[i].style.display = txtValue.toLowerCase().indexOf(input) > -1 ? "" : "none";
    }
  }
}

// Toggle between Customer and NGO tables
function showCustomerTable() {
  document.getElementById("customerTable").style.display = "block";
  document.getElementById("ngoTable").style.display = "none";
  document.getElementById("customerSearchPanel").style.display = "block";
  document.getElementById("ngoSearchPanel").style.display = "none";
}

function showNgoTable() {
  document.getElementById("customerTable").style.display = "none";
  document.getElementById("ngoTable").style.display = "block";
  document.getElementById("customerSearchPanel").style.display = "none";
  document.getElementById("ngoSearchPanel").style.display = "block";
}
