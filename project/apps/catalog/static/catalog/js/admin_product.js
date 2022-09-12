document.addEventListener("DOMContentLoaded", function(event) { 
    var price = document.getElementById('id_price')
    var old_price = document.getElementById('id_old_price')

    function calc_discount() {
    let price = parseFloat(document.getElementById('id_price').value);
    let old_price = parseFloat(document.getElementById('id_old_price').value);
    let result_field = document.querySelector('.field-discount_price .readonly');
    if (old_price > price)
    {
        result = Math.round((1 - price/old_price) * 100);
        result_field.textContent = result + ' %';
    }
    else result = 100;
    result_field.textContent = result + ' %';
    
    }

    price.addEventListener('input', calc_discount);
    old_price.addEventListener('input', calc_discount);
  });