 $(document).ready(function(){
var stripeFormModule=$(".stripe-paymment-form")
var stripeToken=stripeFormModule.attr('data-token')
var stripeNextUrl=stripeFormModule.attr('data-next-url')
var stripeTemplate=$.templates("#stripeTemplate")
var stripeTemplateDataContext=({
  publish_key:stripeToken,
  next_url:stripeNextUrl,
})
var stripeTemplateHtml=stripeTemplate.render(stripeTemplateDataContext)
stripeFormModule.html(stripeTemplateHtml)


var paymentForm=$('.payment-form')
if(paymentForm.length >1 ){
  alert('Multiple payment form is not allowed.')
  paymentForm.css('display','none')
}else if (paymentForm.length == 1){

var pubKey=paymentForm.attr('data-token')
var nextUrl=paymentForm.attr('data-next-url')
// Create a Stripe client
var stripe = Stripe(pubKey);

// Create an instance of Elements
var elements = stripe.elements();

// Custom styling can be passed to options when creating an Element.
// (Note that this demo uses a wider set of styles than the guide below.)
var style = {
  base: {
    color: '#32325d',
    lineHeight: '18px',
    fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
    fontSmoothing: 'antialiased',
    fontSize: '16px',
    '::placeholder': {
      color: '#aab7c4'
    }
  },
  invalid: {
    color: '#fa755a',
    iconColor: '#fa755a'
  }
};

// Create an instance of the card Element
var card = elements.create('card', {style: style});

// Add an instance of the card Element into the `card-element` <div>
card.mount('#card-element');

// Handle real-time validation errors from the card Element.
card.addEventListener('change', function(event) {
  var displayError = document.getElementById('card-errors');
  if (event.error) {
    displayError.textContent = event.error.message;
  } else {
    displayError.textContent = '';
  }
});

// Handle form submission
var form = $('#payment-form');
form.on('submit', function(event) {
  event.preventDefault();
  var $this=$(this)
  var btnLoad=$this.find('.btn-load')
  var loadTime=1500
  var errorHtml="<i class='fa fa-warning'></i>An Error"
  var errorClass="btn btn-danger disabled my-3"
  var loadingHtml="<i class='fa fa-spin fa-spinner'></i>Loading"
  var loadingClass="btn btn-success disabled my-3"
  stripe.createToken(card).then(function(result) {
    if (result.error) {
      // Inform the user if there was an error
      var errorElement = $('#card-errors');
      errorElement.textContent = result.error.message;
    } else {
      // Send the token to your server
      stripeTokenHandler(result.token);
    }
  });
});

function displayBtnStatus(element,newHtml,newClass,loadTime){
  var defaultHtml=element.html()
  var defaultClass=elsment.attr('class')
  element.html(newHtml)
  element.removeClass(defaultClass)
  element.addClass(newClass)
  setTimeout(function(){
    element.html(defaultHtml)
    element.removeClass(newClass)
    element.addClass(defaultClass)   
  },loadTime)

}

function redirectNext(nextpath,timeoffset){
      if(nextpath){
        setTimeout(function(){
          window.location.href=nextpath
        },timeoffset)   
      }    
}
function stripeTokenHandler(token){
  var paymentMethodEndpoint='/billing/pay/create/'
  var data={
    'token':token.id
  }
  $.ajax({
    url:paymentMethodEndpoint,
    data:data,
    method:"POST",
    success:function(data){
      card.clear()
      $.alert({
        title:"<i class='fa fa-spin fa-spinner'></i>Redirecting...",
        content:"Success,your card has been added.",
        theme:'modern',
      })
      redirectNext(nextUrl,1500)   
    },
    error:function(error){
      console.log('error')
      console.log(error)
    }
  })
}
}

})

