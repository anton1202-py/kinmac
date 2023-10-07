// =========== ВЫВЕДЕНИЕ ФОРМ В ЗАВИСИМОСТИ ОТ ВЫБОРА ==========
var paymentsForm = document.forms['payments'];
if (paymentsForm) {
    if (document.forms.payments.elements[3]) {
        const select1 = document.forms.payments.elements[3];
        select1.onchange = function(){ 
            let options = select1.options; 
            let index = select1.selectedIndex; 

            if(options[index].textContent === 'Оплата по расчетному счету'){ 
                document.getElementById('pay_with_checking_account').style.display = "";} 
            else { 
                document.getElementById('pay_with_checking_account').style.display = "none"; 
                document.getElementById('id_contractor_name').removeAttribute('required'); 
                document.getElementById('id_contractor_bill_number').removeAttribute('required'); 
                document.getElementById('id_contractor_bik_of_bank').removeAttribute('required'); 
                document.getElementById('id_file_of_bill').removeAttribute('required');} 
            if(options[index].textContent === 'Оплата картой на сайте'){ 
                document.getElementById('pay_with_card').style.display = "";} 
            else { 
                document.getElementById('pay_with_card').style.display = "none";} 
            if(options[index].textContent === 'Перевод на карту'){ 
                document.getElementById('transfer_to_card').style.display = "";} 
            else { 
                document.getElementById('transfer_to_card').style.display = "none"; 
                document.getElementById('id_phone_number').removeAttribute('required'); 
                document.getElementById('id_bank_for_payment').removeAttribute('required');} 
            if(options[index].textContent === 'Оплата наличными'){ 
                document.getElementById('cash_payment').style.display = "";} 
            else { 
                document.getElementById('cash_payment').style.display = "none";} 
        };
    }
} else {
  console.error('Элемент payments не найден на странице');
}

//  =========== РАБОТА С POP UP ОКНОМ =========
// Получаем элементы кнопки и pop up окна
var popupButton = document.getElementById('popup-button');
var popupContainer = document.getElementById('popup-container');

// При клике на кнопку открываем pop up окно
if (popupButton && popupContainer){
popupButton.addEventListener('click', function() {
  popupContainer.style.display = 'block';
});
function closePopup() {
  document.getElementById("popup-container").style.display = "none";
}
} else {
  console.error('Элементы popup-button и popup-container не найдены на странице');
}


//  =========== ВЫДЕЛЕНИЕ  КРАСНЫМ ЦВЕТОМ ОТКЛОНЕННЫХ ЗАЯВОК =========
const elements = document.getElementsByTagName("th");
const values = document.getElementsByTagName("td");
const table = document.querySelector('table')

if (elements && values && table) {
  for (var element = 0; element < elements.length; ++element) {
    if (elements[element].textContent === 'Причина отклонения') {
      for (var value = 1; value < table.rows.length; ++value) {
          row = table.rows[value];
          if (row.cells[element] && row.cells[element].textContent !== 'None') {
          table.rows[value].style.background = '#fcdcdc'
          }}
      }
  }
} else {
  console.error('Элементы th, td и table не найдены на странице');
}
