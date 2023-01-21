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
}

function recomputeCosts() {
    //Recompute costs
    let prices = Array.from(document.getElementsByClassName("price-text"));
    let amounts = Array.from(document.getElementsByClassName("amount-box"));
    let costs = Array.from(document.getElementsByClassName("cost-text"));

    prices.sort(compare_ids);
    amounts.sort(compare_ids);
    costs.sort(compare_ids);

    let sum = 0

    for(let i=0; i<prices.length; i++) {
        let price = prices[i].innerHTML;
        let amount = amounts[i].value;

        let current_cost = parseFloat(price) * parseFloat(amount);
        sum += current_cost;

        costs[i].innerHTML = current_cost.toFixed(2).toString();
    }

    //Recompute total value
    let total = document.getElementById("total-cost");
    total.innerHTML = sum.toFixed(2).toString();
}

function compare_ids(a, b) {
    if (a.id < b.id) {
        return -1;
    }
    if (a.id > b.id) {
        return 1;
    }
    return 0;
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
    recomputeCosts();
}