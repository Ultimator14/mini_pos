/*
 * Service Table
 */

function compare_ids(a, b) {
    if (a.id < b.id) {
        return -1;
    }
    if (a.id > b.id) {
        return 1;
    }
    return 0;
}

function updateValues() {
    let classes = [
        "amount-box",
        "amount2-text",
        "comment-box",
        "cost-text",
        "product-name",
        "price-text",
        "product-row"
    ];

    let clselements= classes.map(cls => Array.from(document.getElementsByClassName(cls)));
    clselements.forEach((cls) => cls.sort(compare_ids));
    let [amounts, amounts2, comments, costs, names, prices, rows] = clselements;

    let sum = 0;
    let overview = document.getElementById("overview");

    overview.innerHTML = "";  //clear children of overview list

    for(let i=0; i<prices.length; i++) {
        //Extract values
        let amount = amounts[i].value;
        let comment = comments[i].value;
        let name = names[i].innerHTML;
        let price = prices[i].innerHTML;

        //Catch negative values
        if (amount < 0) {
            amount = 0;
            amounts[i].value = 0;
        }

        //Compute per product cose and accumulation
        let current_cost = parseFloat(price) * parseFloat(amount);
        sum += current_cost;

        //Set cost field
        costs[i].innerHTML = current_cost.toFixed(2).toString();

        //Sync second amount field
        amounts2[i].innerHTML = amount;

        //Colorize table row if amount is > 0
        if (parseFloat(amount) > 0) {
            rows[i].classList.add("colorized-row");

            //Generate overview
            let entry = document.createElement('li');
            let entry2 = document.createElement('li');

            let entry_text = amount + "x " + name
            entry_text += (comment !== "" ? " (" + comment + ")" : "");
            let entry_text2 = current_cost.toFixed(2).toString() + "€";

            entry.appendChild(document.createTextNode(entry_text));
            entry2.appendChild(document.createTextNode(entry_text2));

            overview.appendChild(entry);
            overview.appendChild(entry2);
        }
        else {
            rows[i].classList.remove("colorized-row");
        }
    }

    //Recompute total value
    let total = document.getElementById("total-cost");
    total.innerHTML = sum.toFixed(2).toString();
}

function showPopup(pid) {
    /*Display popup*/
    document.getElementById("customize-popup-" + pid).style.display = "block";
}

function hidePopup(pid) {
    /*Colorize Customization button if textbox contains content*/
    let textbox = document.getElementById("comment-" + pid);
    let customizeButton = document.getElementById("customize-button-" + pid);

    if (textbox.value === "") {
        customizeButton.style.backgroundColor = null;
    }
    else {
        customizeButton.style.backgroundColor = "#4CAF50";
    }

    /*Hide popup*/
    document.getElementById("customize-popup-" + pid).style.display = "none";

    updateValues();
}

function modifyAmount(pid, value) {
    //Modify current value
    let textbox = document.getElementById("amount-" + pid);
    let current_value = parseInt(textbox.value);
    let new_value;

    if (isNaN(current_value)) {
        new_value = 0;
    } else {
        new_value = current_value + value;
    }

    if (new_value <= 0) {
        new_value = 0;
    }

    textbox.value = new_value;
    updateValues();
}

function toggleCategoryFold(pcat) {
    let cfd = document.getElementById("category-fold-div-" + pcat);
    let cfb = document.getElementById("category-button-" + pcat);

    if (! cfd.classList.contains("hidden")) {
        //Element is shown and will be hidden
        //Set max height for later unfold
        cfd.classList.remove("category-fold-div");  //disable transitions for this step
        cfd.style.maxHeight = cfd.offsetHeight + "px";
        cfd.classList.add("category-fold-div");  //reenable transitions
    }

    ["transitionEnd", "webkitTransitionEnd", "transitionend", "oTransitionEnd", "msTransitionEnd"].forEach(function(e) {
        cfd.addEventListener(e, function() {
            if(! cfd.classList.contains("hidden")){
                //Element was hidden and is shown, transition is over
                cfd.style.maxHeight = "";  //Reset max-height to allow element to resize to auto
            }
        });
    });

    //Set a small timeout (1ms probably also works but we use 10ms to be sure)
    //If the reenable transitions step comes too quick before a event that would enable
    //transitions, the transition will not fire. With the timeout the browser has enough
    //time to enable the transition
    setTimeout(function(){
        cfd.classList.toggle("hidden");
        cfb.classList.toggle("arrowturn");
    }, 10);
}

function initialCategoryFold() {
    let divs = document.getElementsByClassName("category-fold-div");
    let buttons = document.getElementsByClassName("category-button");

    //Set height and hide by default
    for(let i=0; i<divs.length; i++) {
        divs[i].style.maxHeight = divs[i].offsetHeight + "px";
        divs[i].classList.toggle("hidden");
    }
    //Turn arrows to correct position
    for(let i=0; i<buttons.length; i++) {
        buttons[i].classList.toggle("arrowturn");
    }
}

/*
 * Service Overview
 */

function updateValues2() {
    let classes = [
        "amount-box",
        "product-name",
        "product-price",
        "product-row"
    ];

    let clselements= classes.map(cls => Array.from(document.getElementsByClassName(cls)));
    clselements.forEach((cls) => cls.sort(compare_ids));
    let [amounts, names, prices, rows] = clselements;

    let sum = 0;
    let overview = document.getElementById("overview");

    overview.innerHTML = "";  //clear children of overview list

    for(let i=0; i<prices.length; i++) {
        //Catch negative values
        if (amounts[i].value < 0) {
            amounts[i].value = 0;
        }

        //Extract values
        let amount = amounts[i].value;
        let name = names[i].innerHTML;
        let price = prices[i].innerHTML;

        //Compute accumulation
        let current_cost = parseFloat(price) * parseFloat(amount);
        sum += current_cost;

        //Colorize table row if amount is > 0
        if (parseFloat(amount) > 0) {
            //rows[i].classList.add("colorized-row");  TODO

            //Generate overview
            let entry = document.createElement('li');
            let entry2 = document.createElement('li');

            let entry_text = amount + "x " + name;
            let entry_text2 = current_cost.toFixed(2).toString() + "€";

            entry.appendChild(document.createTextNode(entry_text));
            entry2.appendChild(document.createTextNode(entry_text2));
            overview.appendChild(entry);
            overview.appendChild(entry2);
        }
        else {
            //rows[i].classList.remove("colorized-row");  TODO
        }
    }

    //Recompute total value
    let total = document.getElementById("total-cost");
    total.innerHTML = sum.toFixed(2).toString();
}

function modifyAmount2(pid, value) {
    //Modify current value
    let textbox = document.getElementById("amount-" + pid);
    let span = document.getElementById("max-amount-" + pid);

    let current_value = parseInt(textbox.value);
    let max_value = parseInt(span.innerHTML);
    let new_value;

    if (isNaN(current_value)) {
        new_value = 0;
    } else if (current_value + value > max_value) {
        new_value = current_value;
    } else {
        new_value = current_value + value;
    }

    if (new_value <= 0) {
        new_value = 0;
    }

    textbox.value = new_value;
    updateValues2();
}

function payPartially() {
    let classes = [
        "amount-box",
        "max-amount",
        "product-row"
    ];

    let clselements= classes.map(cls => Array.from(document.getElementsByClassName(cls)));
    clselements.forEach((cls) => cls.sort(compare_ids));
    let [amounts, max_amounts, rows] = clselements;

    for(let i=0; i<rows.length; i++) {
        //Extract values
        let amount = amounts[i].value;
        let max_amount = max_amounts[i].innerHTML;

        if (parseFloat(amount) == parseFloat(max_amount)) {
            //Remove line
            rows[i].remove();

        } else if (parseFloat(amount) > 0) {
            //Reset amount, update max_amount
            amounts[i].value = 0;
            max_amounts[i].innerHTML = max_amount - amount;
        }
    }

    //Clear overview and total value
    document.getElementById("overview").innerHTML = "";
    document.getElementById("total-cost").innerHTML = Number(0).toFixed(2).toString();

    //Check if last product is completed
    if (document.getElementsByClassName("product-row").length == 0) {
        location.href = '/service';
    }
}
