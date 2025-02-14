/* Max safe int, above there are rounding errors */
const MAX_INT = 9007199254740991;

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

function getElementsByClass(classlist) {
    let clselements= classlist.map(cls => Array.from(document.getElementsByClassName(cls)));
    clselements.forEach((cls) => cls.sort(compare_ids));
    return clselements;
}

function computeModifyAmountValue(current_value, value_change, max_value) {
    if (isNaN(current_value)) {
        return 0;
    }

    current_value = Number(current_value);
    value_change = Number(value_change);
    max_value = Number(max_value);

    if (current_value + value_change > MAX_INT) {
        return MAX_INT;
    }

    if (current_value + value_change > max_value) {
        return max_value;
    }

    if (current_value + value_change < 0) {
        return 0;
    }

    return current_value + value_change;
}

function fixNumFormat(textbox) {
    //Catch NaN's
    if (isNaN(textbox.value)) {
        textbox.value = 0;
    }

    //Catch 0x..., 0b...
    if (textbox.value != String(Number(textbox.value))) {
        textbox.value = Number(textbox.value);
    }

    //Catch negative values
    if (Number(textbox.value) < 0) {
        textbox.value = 0;
    }

    //Catch values > max int
    if (Number(textbox.value) > MAX_INT) {
        textbox.value = MAX_INT;
    }
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

    let [amounts, amounts2, comments, costs, names, prices, rows] = getElementsByClass(classes);

    let sum = 0;
    let overview = document.getElementById("overview");

    overview.innerHTML = "";  //clear children of overview list

    for(let i=0; i<prices.length; i++) {
        fixNumFormat(amounts[i]);

        //Extract values
        let amount = Number(amounts[i].value);
        let comment = comments[i].value;
        let name = names[i].innerHTML;
        let price = parseFloat(prices[i].innerHTML);

        //Compute per product cose and accumulation
        let current_cost = price * amount;
        sum += current_cost;

        //Set cost field
        costs[i].innerHTML = current_cost.toFixed(2).toString();

        //Sync second amount field
        amounts2[i].innerHTML = amount;

        //Colorize table row if amount is > 0
        if (amount > 0) {
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

    textbox.value = computeModifyAmountValue(current_value, value, MAX_INT);

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
        "max-amount",
        "product-name",
        "product-price",
        "product-row"
    ];

    let [amounts, max_amounts ,names, prices, rows] = getElementsByClass(classes);

    let sum = 0;
    let overview = document.getElementById("overview");

    overview.innerHTML = "";  //clear children of overview list

    for(let i=0; i<prices.length; i++) {
        fixNumFormat(amounts[i]);

        //Catch values > max
        if (Number(amounts[i].value) > Number(max_amounts[i].innerHTML)) {
            amounts[i].value = max_amounts[i].innerHTML;
        }

        //Extract values
        let amount = Number(amounts[i].value);
        let name = names[i].innerHTML;
        let price = parseFloat(prices[i].innerHTML);

        //Compute accumulation
        let current_cost = price * amount;
        sum += current_cost;

        //Colorize table row if amount is > 0
        if (amount > 0) {
            rows[i].classList.add("colorized-row");

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
            rows[i].classList.remove("colorized-row");
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

    textbox.value = computeModifyAmountValue(current_value, value, max_value);

    updateValues2();
}

function payPartially() {
    let classes = [
        "amount-box",
        "max-amount",
        "product-row"
    ];

    let [amounts, max_amounts, rows] = getElementsByClass(classes);

    for(let i=0; i<rows.length; i++) {
        //Extract values
        let amount = Number(amounts[i].value);
        let max_amount = Number(max_amounts[i].innerHTML);

        if (amount == max_amount) {
            //Remove line
            rows[i].remove();

        } else if (amount > 0) {
            //Reset amount, update max_amount, reset colors
            amounts[i].value = 0;
            max_amounts[i].innerHTML = max_amount - amount;
            rows[i].classList.remove("colorized-row");
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

function selectAll() {
    let amounts = Array.from(document.getElementsByClassName("amount-box"));
    let max_amounts = Array.from(document.getElementsByClassName("max-amount"));

    amounts.sort(compare_ids);
    max_amounts.sort(compare_ids);

    //Set amount = max_amount for all products
    for(let i=0; i<amounts.length; i++) {
        amounts[i].value = max_amounts[i].innerHTML;
    }

    updateValues2();
}

function unselectAll() {
    let amounts = Array.from(document.getElementsByClassName("amount-box"));

    //Set amount = 0 for all products
    for(let i=0; i<amounts.length; i++) {
        amounts[i].value = 0;
    }

    updateValues2();
}
