// Main JavaScript file

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Confirm delete actions
    var deleteButtons = document.querySelectorAll('.delete-confirm');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item?')) {
                e.preventDefault();
            }
        });
    });
    
    // Cart quantity update
    var quantityInputs = document.querySelectorAll('.cart-quantity');
    quantityInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            var productId = this.dataset.productId;
            var quantity = this.value;
            updateCart(productId, quantity);
        });
    });
    
    // Search form enhancement
    var searchForm = document.querySelector('form[action*="products"]');
    if (searchForm) {
        var searchInput = searchForm.querySelector('input[name="search"]');
        var searchButton = searchForm.querySelector('button[type="submit"]');
        
        // Disable search button if input is empty
        if (searchInput && searchButton) {
            searchInput.addEventListener('input', function() {
                searchButton.disabled = this.value.trim() === '';
            });
        }
    }
    
    // Lazy loading images
    var lazyImages = [].slice.call(document.querySelectorAll('img[loading="lazy"]'));
    if ('IntersectionObserver' in window) {
        let lazyImageObserver = new IntersectionObserver(function(entries, observer) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    let lazyImage = entry.target;
                    lazyImage.src = lazyImage.dataset.src;
                    lazyImage.classList.remove('lazy');
                    lazyImageObserver.unobserve(lazyImage);
                }
            });
        });
        
        lazyImages.forEach(function(lazyImage) {
            lazyImageObserver.observe(lazyImage);
        });
    }
});

// AJAX function to update cart
function updateCart(productId, quantity) {
    fetch('/update-cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update cart total
            var cartTotal = document.getElementById('cart-total');
            if (cartTotal) {
                cartTotal.textContent = '₦' + data.total.toFixed(2);
            }
            
            // Update cart count in navbar
            var cartCount = document.querySelector('.badge.bg-danger');
            if (cartCount) {
                cartCount.textContent = data.count;
            }
        }
    })
    .catch(error => console.error('Error:', error));
}

// Show loading spinner
function showLoading() {
    var spinner = document.getElementById('loading-spinner');
    if (spinner) {
        spinner.style.display = 'flex';
    }
}

// Hide loading spinner
function hideLoading() {
    var spinner = document.getElementById('loading-spinner');
    if (spinner) {
        spinner.style.display = 'none';
    }
}

// Add to cart with animation
function addToCart(productId, productName) {
    showLoading();
    
    fetch('/add-to-cart/' + productId, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'quantity=1'
    })
    .then(response => {
        hideLoading();
        if (response.redirected) {
            window.location.href = response.url;
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error:', error);
        alert('Error adding item to cart');
    });
}

// Price formatting
function formatPrice(price) {
    return '₦' + parseFloat(price).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
}

// Validate phone number
function validatePhone(phone) {
    var phoneRegex = /^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$/;
    return phoneRegex.test(phone);
}

// Initialize on page load
window.onload = function() {
    // Add loading spinner to body
    var spinner = document.createElement('div');
    spinner.id = 'loading-spinner';
    spinner.className = 'spinner-wrapper';
    spinner.innerHTML = '<div class="loading-spinner"></div>';
    document.body.appendChild(spinner);
    
    // Add lazy loading to product images
    var productImages = document.querySelectorAll('.product-card img, .product-gallery img');
    productImages.forEach(function(img) {
        if (!img.hasAttribute('loading')) {
            img.setAttribute('loading', 'lazy');
        }
    });
};

// Handle form submission for WhatsApp orders
function handleWhatsAppOrder(form) {
    showLoading();
    return true; // Allow form to submit
}