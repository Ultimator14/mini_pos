let myTimer = setInterval(updateActiveTables, 3000);

async function updateActiveTables() {
    //Request new tables
    const response = await fetch("/fetch/service");
    const tables_new_ids = await response.json();

    //Get table elements
    let tables_cur = Array.from(document.getElementsByClassName("active-order"));
    let tables_new = [];
    for(let i=0; i<tables_new_ids.length; i++) {
        tables_new.push(document.getElementById(tables_new_ids[i]))
    }

    //Get tables updates
    let added_tables = tables_new.filter(x => ! tables_cur.includes(x));
    let removed_tables = tables_cur.filter(x => ! tables_new.includes(x));

    //Reset removed tables
    for(let i=0; i<removed_tables.length; i++) {
        removed_tables[i].classList.remove("active-order");
        removed_tables[i].classList.add("no-order");
    }

    //Set active tables to active
    for(let i=0; i<added_tables.length; i++) {
        added_tables.classList.remove("no-order");
        added_tables.classList.add("active-order");
    }
}
