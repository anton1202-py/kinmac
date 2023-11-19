// =========== ВЫВЕДЕНИЕ ФОРМ В ЗАВИСИМОСТИ ОТ ВЫБОРА ==========
var paymentsForm = document.forms['payments'];
if (paymentsForm) {
    if (paymentsForm.elements[8]) {
        const select1 = paymentsForm.elements[10];
        select1.onchange = function(){ 
            let options = select1.options; 
            let index = select1.selectedIndex; 

            if(options[index].textContent === 'Оплата по расчетному счету'){ 
                document.getElementById('pay_with_checking_account').style.display = "";} 
            else { 
              document.getElementById('pay_with_checking_account').style.display = "none";
              document.getElementById('id_file_of_bill').removeAttribute('required');} 
            if(options[index].textContent === 'Оплата по карте на сайте'){ 
                document.getElementById('pay_with_card').style.display = "";} 
            else { 
                document.getElementById('pay_with_card').style.display = "none";} 
            if(options[index].textContent === 'Перевод на карту'){ 
                document.getElementById('transfer_to_card').style.display = "";} 
            else { 
                document.getElementById('transfer_to_card').style.display = "none"; 
                document.getElementById('id_phone_number').removeAttribute('required'); 
                document.getElementById('id_bank_for_payment').removeAttribute('required');} 
            if(options[index].textContent === 'Наличная оплата'){ 
                document.getElementById('cash_payment').style.display = "";} 
            else { 
                document.getElementById('cash_payment').style.display = "none";} 
        };
    }
} else {
  console.error('Элемент payments не найден на странице');
}

//  =========== РАБОТА С POP UP ОКНОМ ПО ОТКЛОНЕНИЮ ЗАЯВКИ =========
// Получаем элементы кнопки и pop up окна
var popupButtons = document.querySelectorAll('[id="popup-button"]');
var popupContainer = document.getElementById('popup-container');

// При клике на кнопку открываем pop up окно
if (popupButtons && popupContainer){
    popupButtons.forEach(function(button) {
      button.addEventListener('click', function()  {
        popupContainer.style.display = '';
        var row = this.closest('tr');
        var rowIndex = Array.from(row.parentNode.children).indexOf(row) + 1
        var firstCellValue = row.cells[0].innerText
        // Присваиваю нажимаемой кнопке значение ID с первого столбца таблицы
        document.getElementById('reject_payment_id').value = firstCellValue
      })
    });
function closePopup() {
  document.getElementById("popup-container").style.display = "none";
}
} else {
  console.error('Элементы popup-button и popup-container не найдены на странице');
}


//  =========== РАБОТА С POP UP ОКНОМ ПО ОПЛАТЕ ЗАЯВКИ =========
// Получаем элементы кнопки и pop up окна
var popupPayButtons = document.querySelectorAll('[id="popup-pay-button"]');
var popupPayContainer = document.getElementById('popup-pay-container');

// При клике на кнопку открываем pop up окно
if (popupPayButtons && popupPayContainer){
    popupPayButtons.forEach(function(button) {
      button.addEventListener('click', function()  {
        popupPayContainer.style.display = '';
        var rowPay = this.closest('tr');
        var rowIndex = Array.from(rowPay.parentNode.children).indexOf(rowPay) + 1
        var firstCellValue = rowPay.cells[0].innerText
        var lastCellValue = rowPay.cells[17].innerText
        if (lastCellValue === 'True') {
          document.getElementById('id-form-pay_payment-add-file').style.display = 'block';
        }
        console.log(lastCellValue)
        // Присваиваю нажимаемой кнопке значение ID с первого столбца таблицы
        document.getElementById('pay_payment_id').value = firstCellValue
      })
    });
function closePopup() {
  document.getElementById("popup-pay-container").style.display = "none";
}
} else {
  console.error('Элементы popup-pay-button и popup-pay-container не найдены на странице');
}


//  =========== ВЫДЕЛЕНИЕ  КРАСНЫМ ЦВЕТОМ ОТКЛОНЕННЫХ ЗАЯВОК =========
const elements = document.getElementsByTagName("th");
const values = document.getElementsByTagName("td");
const table = document.querySelector('table')

if (elements && values && table) {
  for (var element = 0; element < elements.length; ++element) {
    if (elements[element].textContent === 'Статус') {
      for (var value = 1; value < table.rows.length; ++value) {
          row = table.rows[value];
          if (row.cells[element] && row.cells[element].textContent.includes('Отклонено')) {
          table.rows[value].style.background = '#ffeded'
          };
          if (row.cells[element] && row.cells[element].textContent.includes('Оплачено')) {
            table.rows[value].style.background = '#e3fcd9'
            };}
      }
  }
} else {
  console.error('Элементы th, td и table не найдены на странице');
}




