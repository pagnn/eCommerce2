$(document).ready(function(){
      //auto-search//
      var searchForm=$('.search-form')
      var searchInput=searchForm.find("[name='q']")
      var typingTimer
      var typingInterval=1500
      var searchBtn=searchForm.find("[type='submit']")
      searchInput.keyup(function(event){
        clearTimeout(typingTimer)
        typingTimer=setTimeout(performSearch,typingInterval)
        
      })
      searchInput.keydown(function(event){
        clearTimeout(typingTimer)       
      })
      function displaySearching(){
        searchBtn.addClass('disabled')
        searchBtn.html("<i class='fa fa-spin fa-spinner'></i>Searching...")       
      }
      function performSearch(){
        displaySearching()
        var query=searchInput.val()
        setTimeout(function(){
          window.location.href='/search/?q='+query 
        },1000)
              
      }

      //contact form//
      var contactForm=$('.contact-form')
      var contactFormMethod=contactForm.attr('method')
      var contactFormEndpoint=contactForm.attr('action')

      function displaySubmit(submitbtn,defaultText,doSubmit){
        if (doSubmit){
          submitbtn.addClass('disabled')
          submitbtn.html("<i class='fa fa-spin fa-spinner'></i>Sending...") 
        }else{
          submitbtn.removeClass('disabled')
          submitbtn.html(defaultText)
        }
              
      }  
      contactForm.submit(function(event){
        event.preventDefault()
        var contactFormData=contactForm.serialize()
        var thisForm=$(this)
        var contactFormBtn=contactForm.find("[type='submit']")
        var contactFormBtntxt=contactFormBtn.text()
        displaySubmit(contactFormBtn,'',true)
        $.ajax({
          url:contactFormEndpoint,
          method:contactFormMethod,
          data:contactFormData,
          success:function(data){
            contactForm[0].reset()
            $.alert({
              title: 'Success!',
              content: data.message,
              theme:'modern',
            });
            setTimeout(function(){displaySubmit(contactFormBtn,contactFormBtntxt,false)},500)               
          },
          error:function(errordata){
            console.log(errordata.responseJSON)
            var json_data=errordata.responseJSON
            var msg=''
            $.each(json_data,function(key,value){
              msg+=key+':'+value[0].message
            })
            $.alert({
              title: 'Oops!',
              content:msg,
              theme:'modern',
            });
            setTimeout(function(){displaySubmit(contactFormBtn,contactFormBtntxt,false)},500)             
          }
        })
      })



      //ajax//
      var productForm=$('.form-product-ajax')

      function getOwnedProduct(productId,submitSpan){
        var actionEndpoint='/orders/endpoint/verify/ownership/'
        var httpMethod='GET'
        var data={
          product_id:productId
        }
        var isOwner;
        $.ajax({
          url:actionEndpoint,
          data:data,
          method:httpMethod,
          success:function(data){
            console.log(data.owner)
            if(data.owner){
              isOwner = true
              submitSpan.html("<a class='btn btn-link' href='/library/'>In Library</a>")
            }
            else{
              isOwner = false
            }
          },
          error:function(error){
          },
        })
      }
      $.each(productForm,function(index,object){
        var $this=$(this)
        var isUser=$this.attr('data-user')
        var submitSpan=$this.find('.submit-span')
        var productInput=$this.find("[name='product_id']")
        var productId=productInput.attr('value')
        var productIsDigital=productInput.attr('data-is-digital')
        if (productIsDigital && isUser){
         getOwnedProduct(productId,submitSpan) 
        }
      })






      productForm.submit(function(event){
        event.preventDefault();
        var thisForm=$(this);
        var actionEndpoint=thisForm.attr('data-endpoint');
        var httpMethod=thisForm.attr('method');
        var formData=thisForm.serialize();
        $.ajax({
          url:actionEndpoint,
          method:httpMethod,
          data:formData,
          success:function(data){
            var submitSpan=thisForm.find('.submit-span')
            if(data.added){
              submitSpan.html("<div class='button-group'><a href='/carts/' class='btn btn-link'>In cart</a><button type='submit' class='btn btn-link'>Remove</button></div>")
            }else{
              submitSpan.html("<button type='submit' class='btn btn-success'>Add to cart</button>")
            }

            var navbarCount=$('.navbar-cart-count')
            navbarCount.text(data.cartItemsCount)

            var currentPath=window.location.href
            if (currentPath.indexOf('carts') != -1){
              refreshCart()
            }
          },
          error:function(errordata){
            $.alert({
              title: 'Oops!',
              content: 'An error occurred!',
              theme:'modern',
            });
          }
        })

      })
      function refreshCart(){
        console.log('in current cart')
        var cartTable=$('.cart-table')
        var cartBody=cartTable.find('.cart-body')
        var refreshCartUrl='/carts/api/'
        var refreshCartMethod='GET'
        var data={}
        $.ajax({
          url:refreshCartUrl,
          method:refreshCartMethod,
          data:data,
          success:function(data){
            var hiddenCartItemRemoveForm=$('.cart-remove-form')
            if(data.products.length>0){
              var cartProducts=cartTable.find('.cart-products')
              cartProducts.html('')
              i=data.products.length
              $.each(data.products,function(index,value){
                console.log(value)
                var CartItemRemoveForm=hiddenCartItemRemoveForm.clone()
                CartItemRemoveForm.css('display','block')
                CartItemRemoveForm.find('.cart-product-id').val(value.id)
                cartBody.prepend("<tr><th scope=\"row\">"+i+"</th><td><a href='"+value.url+"'>"+value.name+"</a>"+CartItemRemoveForm.html()+"</td><td>"+value.price+"</td></tr>")
                i--
              })
              
              var cartSubtotal=cartTable.find('.cart-subtotal')
              var cartTotal=cartTable.find('.cart-total')
              cartTotal.text(data.total)
              cartSubtotal.text(data.subtotal)
            }else{
              window.location.href='/carts/'
            }
          },
          error:function(errordata){
            $.alert({
              title: 'Oops!',
              content: 'An error occurred!',
              theme:'modern',
            });
          }
        })
      }
    })