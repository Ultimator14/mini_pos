let myTimer = setInterval(updateActiveTables, 1000);

async function updateActiveTables() {
    //Request new tables
    const response = await fetch("/fetch/service");
    const tables_new = await response.json();

    //Reset all tables
    let tables_cur = Array.from(document.getElementsByClassName("active-order"));

    for(let i=0; i<tables_cur.length; i++) {
        tables_cur[i].classList.remove("active-order");
        tables_cur[i].classList.add("no-order");
    }

    //Set active tables to active
    for(let i=0; i<tables_new.length; i++) {
        let table = document.getElementById(tables_new[i]);
        table.classList.remove("no-order");
        table.classList.add("active-order");
    }
}
