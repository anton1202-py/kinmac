const paymentsForm = document.forms.payments

const select2 = document
//console.log(select2)
var ids = document.querySelectorAll('[name]');
console.log( ids )

Array.prototype.forEach.call( ids, function( el, i ) {
    console.log( el.name ); // log the ID
});
const select1 = document.forms.payments.elements[3]

var comment1 = document.getElementById('but')
console.log(comment1)

document.getElementsByName('comment').style.display = "none"
document.getElementById('reject_payment_id').onclick=function(){
    // Remove any element-specific value, falling back to stylesheets
    document.getElementById('comment_reject_payment_text').style.display='none';
  };


var node = document.getElementById('pay_with_card')
htmlContent = node.innerHTML

select1.onchange = function(){
    let options = select1.options
    let index = select1.selectedIndex

    //console.log(index);
    //console.log(options[index].textContent);
    if(options[index].textContent === 'Оплата по расчетному счету'){
        document.getElementById('pay_with_checking_account').style.display = ""}
    else {
        document.getElementById('pay_with_checking_account').style.display = "none";
        document.getElementById('id_contractor_name').removeAttribute('required');
        document.getElementById('id_contractor_bill_number').removeAttribute('required');
        document.getElementById('id_contractor_bik_of_bank').removeAttribute('required');
        document.getElementById('id_file_of_bill').removeAttribute('required')};
    if(options[index].textContent === 'Оплата по карте на сайте'){
        document.getElementById('pay_with_card').style.display = ""}
    else {
        document.getElementById('pay_with_card').style.display = "none"};
    if(options[index].textContent === 'Перевод на карту'){
        document.getElementById('transfer_to_card').style.display = ""}
    else {
        document.getElementById('transfer_to_card').style.display = "none";
        document.getElementById('id_phone_number').removeAttribute('required');
        document.getElementById('id_bank_for_payment').removeAttribute('required');};
    if(options[index].textContent === 'Наличная оплата'){
        document.getElementById('cash_payment').style.display = ""}
    else {
        document.getElementById('cash_payment').style.display = "none"};
}


const select3 = document.forms
console.log( select3 );