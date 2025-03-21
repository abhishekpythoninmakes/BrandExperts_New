$(document).ready(function() {
    console.log('product_details.js loaded');

    $('#id_product').change(function() {
        console.log('Product selection changed');
        var productId = $(this).val();
        if (productId) {
            console.log('Fetching product details for ID:', productId);
            $.ajax({
                url: `/admin/products_app/standard_sizes/get-product-details/`,
                data: { 'product_id': productId },
                success: function(data) {
                    console.log('Product details received:', data);
                    var detailsHtml = `
                        Size: ${data.size}<br>
                        Min Width: ${data.min_width} ${data.size}<br>
                        Max Width: ${data.max_width} ${data.size}<br>
                        Min Height: ${data.min_height} ${data.size}<br>
                        Max Height: ${data.max_height} ${data.size}
                    `;
                    $('#id_product_details').html(detailsHtml);
                },
                error: function(xhr) {
                    console.error('Error:', xhr.responseText);
                    $('#id_product_details').html('Error loading details');
                }
            });
        } else {
            console.log('No product selected');
            $('#id_product_details').html('No product selected');
        }
    });
});