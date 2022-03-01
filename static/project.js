// In your Javascript (external .js resource or <script> tag)
$(document).ready(function() {

    $(document).mouseup(function(e)
    {
        var container = $(".sidebar");
        var menu_icon =  $('.mobile-menu-icon');
        // if the target of the click isn't the container nor a descendant of the container
        if (!container.is(e.target) && container.has(e.target).length === 0 &&
        !menu_icon.is(e.target) && menu_icon.has(e.target).length === 0
        )
        {
            container.removeClass('active');
        }
    });

    $('.mobile-menu-icon').on('click', function() {
        $('.sidebar').hasClass('active') ? $('.sidebar').removeClass('active') : $('.sidebar').addClass('active')
    })

    $('.select2').select2();

    $(function () {
      $('[data-toggle="popover"]').popover({
         trigger: 'focus'
      })
    })

    $(function () {
      $('[data-toggle="popover-hover"]').popover({
         trigger: 'hover'
      })
    })

    $(".update_trades_for_project").on('change', function(){
        const project_id = $(this).val()

        if (project_id) {
            $(".select_trade_for_bill select").empty()
            $(".select_trade_for_bill select").append($("<option></option>"))
            $('.select_trade_for_bill').removeClass('d-none')
            $.ajax({
              url: '/erp/update_trades_for_project',
              type: "POST",
              dataType: 'json',
              data: {'project_id': project_id},
              success: function(data){
                  for(const trade of data) {
                    $(".select_trade_for_bill select").append($("<option></option>")
                    .attr("value", trade)
                    .text(trade))
                  }
              }
            });
        } else {
            $('.select_trade_for_bill').addClass('d-none')
        }
        $(".select_trade_for_bill select").select2()
   })

   $(".select_trade_for_bill select").on('change', function(){
        const trade = $(this).val()
        if (trade) {
            $(".select_payment_stage select").empty()
            $(".select_payment_stage select").append($("<option></option>"))
            project_id = $("#project").val()
            $('.select_payment_stage').removeClass('d-none')
            $.ajax({
              url: '/erp/update_payment_stages',
              type: "POST",
              dataType: 'json',
              data: {'project_id': project_id, 'trade': trade},
              success: function(data){
                  $('.total_wo_value').text(data['work_order_value'])
                  $('.contractor_name').text(data['contractor_name'])
                  $('.contractor_code').text(data['contractor_code'])
                  $('.contractor_pan').text(data['contractor_pan'])
                  for(const stage of Object.keys(data['stages'])) {
                    $(".select_payment_stage select").append($("<option></option>")
                    .attr("value", data['stages'][stage])
                    .text(stage))
                  }
              }
            });
        } else {
            $('.select_payment_stage').addClass('d-none')
        }
        $(".select_payment_stage select").select2()
   })

   $(".select_payment_stage select").on('change', function(){
        let payment_percentage = $(this).val()
        if (payment_percentage) {

            $(".final_details").removeClass('d-none')
            $(".payment_percentage").text(payment_percentage.toString()+"%")
            let work_order_value = parseFloat($('.total_wo_value').text())
            payment_percentage = parseFloat(payment_percentage)
            const bill_amount_before_5_percent_deduction = (work_order_value * (payment_percentage /  100))
            const final_bill_amount = bill_amount_before_5_percent_deduction - (bill_amount_before_5_percent_deduction * 0.05)
            $(".bill_amount").text(final_bill_amount.toString())
        } else {
            $(".final_details").addClass('d-none')
        }
   })

   $(".create_bill").on('click', function(){
        const project_id = $("#project").val()
        $('input[name="project_id"]').val(project_id)

        const trade = $("#trade").val()
        $('input[name="trade"]').val(trade)

        const stage = $(".select_payment_stage select").find('option:selected').text()
        $('input[name="stage"]').val(stage)

        const payment_percentage = $(".select_payment_stage select").find('option:selected').val()
        $('input[name="payment_percentage"]').val(payment_percentage)

        const amount = $('.bill_amount').text()
        $('input[name="amount"]').val(amount)

        const contractor_name = $('.contractor_name').text()
        $('input[name="contractor_name"]').val(contractor_name)

        const contractor_code = $('.contractor_code').text()
        $('input[name="contractor_code"]').val(contractor_code)

        const contractor_pan = $('.contractor_pan').text()
        $('input[name="contractor_pan"]').val(contractor_pan)

        $("#create_bill_form").submit()
   })

   function updateApprovalModalDetails(clickedBtn) {
        console.log(clickedBtn)
        if ($(clickedBtn).hasClass('approval_1_btn'))
            $('.approval_level').val('Level 1')
        if ($(clickedBtn).hasClass('approval_2_btn'))
            $('.approval_level').val('Level 2')

        const project_id = $(clickedBtn).attr('data-project-id')
        const project_name = $(clickedBtn).attr('data-project-name')
        const bill_id = $(clickedBtn).attr('data-bill-id')
        const contractor_name = $(clickedBtn).parents('tr').find('.contractor_name').text()
        const contractor_code = $(clickedBtn).parents('tr').find('.contractor_code').text()
        const contractor_pan = $(clickedBtn).parents('tr').find('.contractor_pan').text()
        const trade = $(clickedBtn).parents('tr').find('.trade').text()
        const payment_stage = $(clickedBtn).parents('tr').find('.stage').text()
        const amount = $(clickedBtn).parents('tr').find('.amount').text()
        const total_payable = $(clickedBtn).parents('tr').find('.total_payable').text()

        $('#approvalModal .project_name').text(project_name)
        $('#approvalModal .contractor_name').text(contractor_name)
        $('#approvalModal .contractor_code').text(contractor_code)
        $('#approvalModal .contractor_pan').text(contractor_pan)
        $('#approvalModal .trade').text(trade)
        $('#approvalModal .payment_stage').text(payment_stage)
        $('#approvalModal .amount').text(amount)
        $('#approvalModal .total_payable').text(total_payable)
        $('#approvalModal .bill_id').val(bill_id)
        $('#approvalModal .project_id').val(project_id)
   }

   $(".approval_1_btn").on('click', function(){
        const clickedBtn = this
        updateApprovalModalDetails(this)
   })

   $(".approval_2_btn").on('click', function(){
        const clickedBtn = this
        updateApprovalModalDetails(this)
   })

   $(".copy_from_approval_1_btn").on("click", function() {
        updateApprovalModalDetails(this)
        $('.approval_level').val('Level 2')
        const amount_approved = parseFloat($(this).parents("tr").find(".approval_1").text().trim())
        $("#amount_approved").val(amount_approved)
        $('[data-toggle="popover-hover"]').popover('hide')
        saveApprovedBill()
   })

   function populateApprovalAmountInTable(bill_id, amount_approved, approval_level) {
        let tdTagClass = ''
        if (approval_level === 'Level 1')
            tdTagClass = 'approval_1'
        if (approval_level === 'Level 2')
            tdTagClass = 'approval_2'
        $('.bill-'+bill_id.toString()).find('.'+tdTagClass).text(amount_approved)

   }

   function saveApprovedBill() {
        const bill_id = $('#approvalModal .bill_id').val()
        const approved_amount = $("#amount_approved").val()
        const notes = $("#notes").val()
        const approval_level = $('.approval_level').val()
        const project_id = $("#project_id").val()
        const trade =  $('#approvalModal .trade').text()
        const amount = parseFloat($('#approvalModal .total_payable').text())
        const difference_amount = parseFloat(amount) - parseFloat(approved_amount)

        $.ajax({
              url: '/erp/save_approved_bill',
              type: "POST",
              dataType: 'json',
              data: {
                'bill_id': bill_id,
                'approved_amount': approved_amount,
                'notes': notes,
                'approval_level': approval_level,
                'project_id': project_id,
                'trade': trade,
                'difference_amount': difference_amount
              },
              success: function(data){
                $('#approvalModal').modal('hide');
                $('#amount_approved').val('')
                $("#notes").val('')
                $(".approve_bill_btn").text('Approve')
                populateApprovalAmountInTable (bill_id, approved_amount, approval_level)
              }
         });
   }

   function validateApprovedBillAmnt(){
        const amount = parseFloat($('#approvalModal .total_payable').text())
        const approved_amount = parseFloat($("#amount_approved").val())
        if (approved_amount > 0 && approved_amount <= amount ) {
            $('#amount_approved').parent().find('.invalid-message').addClass('d-none')
            return true
        } else {
            $('#amount_approved').parent().find('.invalid-message').text('Amount entered is not valid')
            $('#amount_approved').parent().find('.invalid-message').removeClass('d-none')
        }
        return false;

   }

   $(".approve_bill_btn").on('click', function(){
        if (validateApprovedBillAmnt()) {
            $(".approve_bill_btn").text('...')
            saveApprovedBill()
        }
   })

   function getWorkOrderForSelectedProject() {
        const project = $("#project").val()
        if (project.length) {
            window.location.href = '/erp/view_work_order?project_id='+project.toString()
        }
   }

   $("#view_work_order").on('click', getWorkOrderForSelectedProject)

   function getRevisedDrawingsForSelectedProject() {
        const project = $("#project").val()
        if (project.length) {
            window.location.href = '/erp/revised_drawings?project_id='+project.toString()
        }
   }

   $("#view_revised_drawings").on('click', getRevisedDrawingsForSelectedProject)



   function checkIfNumberOfFloorsUpdated(project_id) {
        $.ajax({
              url: '/erp/check_if_floors_updated',
              type: "POST",
              dataType: 'json',
              data: {
                'project_id': project_id,
              },
              success: function(data){
                if(data['floors_updated']) {
                    $("#floors").val(data['floors'])
                    $(".wo-floors-section").hide()
                } else {
                    $(".wo-floors-section").show()}
              }
         });
   }

   $(".work_order_project_select").on('change', function(){
        const project_id = $(this).val()
        if (project_id) checkIfNumberOfFloorsUpdated(project_id)
   })

   $('.add-elevation-detail').on('click', function() {
        element = $($(this).parent().find('.elevation-details').get(0))
        if (element.hasClass('d-none')) {
            element.removeClass('d-none')
        } else {
            clone = element.clone()
            clone.val('')
            element.parent().append(clone)
        }
        return false
   })

   $('.add-additional-cost').on('click', function() {
        element = $($(this).parent().find('.additional-cost').get(0))
        if (element.hasClass('d-none')) {
            element.removeClass('d-none')
        } else {
            clone = element.clone()
            clone.val('')
            element.parent().append(clone)
        }
        return false
   })

   function populateEDandACfields(ele) {
        elevation_details = $(ele).parents('form').find('.elevation_details_input')

        elevation_details_value = $(ele).parents('form').find('.elevation-details').val()
        $(ele).parents('form').find('.elevation-details').each(function(index, element) {
            if (index != 0)
            elevation_details_value += ' &# ' + element.value
        })
        elevation_details.val(elevation_details_value)




        additional_cost = $(ele).parents('form').find('.additional_cost_input')

        additional_cost_value = $(ele).parents('form').find('.additional-cost').val()
        $(ele).parents('form').find('.additional-cost').each(function(index, element) {
            if (index != 0)
            additional_cost_value += ' &# ' + element.value
        })
        additional_cost.val(additional_cost_value)
        $(ele).parents('form').submit()
   }


   $(".edit_project_submit").on('click', function(event) {
        event.preventDefault()
        populateEDandACfields(this);})

   $('.submit-create-project-form').on('click', function(event) {
        event.preventDefault()
        populateEDandACfields(this);

   })


   drawings = {
            'Architect': [
                'Working drawing (floor plans)',
                'Designer wall details',
                'Filler slab layout',
                'Sections',
                '2 D elevation',
                'Door Window details, Window grill details',
                'Flooring layout details',
                'Toilet,kitchen Dadoing Details',
                'Compound wall details',
                'Fabrication details',
                'Sky light details',
                'External and Internal Paint Shades'
            ],
            'Structural' : [
                'Column Marking',
                'Footing Layout',
                'UG sump details',
                'Plinth Beam layout',
                'Staircase details',
                'Floor form work ,beam and slab reinforcement details',
                'OHT slab details',
                'Lintel details.'
            ],
            'Electrical': [
                'Electrical', 'Conduit'
            ],
            'Plumbing': [
                'Water line drawings',
                'Drainage line drawings',
                'RWH Details'
            ]
        }

   $('#drawing_type').on('change', function() {
        type = $(this).val()
        if (type.length) {
            for(const drawing of drawings[type]) {
                $(".drawing_name_select").append($("<option></option>")
                .attr("value", drawing)
                .text(drawing))
              }
        }
   })

   



});

function onInputNumberInt(value){
    // handle validations
    // allow value to be positive number only
    // use this helper on every int data type 
    value = value.replace(/[^0-9]/g, '');
    return value;
    
}

function onInputNumberFloat(value){
    // handle validations
    // allow value to be positive number only
    // use this helper on every float data type 
    
    if(isNaN(value)){
     value = value.replace(/[^0-9\.]/g,'');
     if(value.split('.').length>2) 
         value =value.replace(/\.+$/,"");
}
    return value;
    
}


function handleNoOfFloorsChange(value){
    // if value is G+1 then set sf_slab_area and tf_slab_area to 0
    // if value is G+2 then set tf_slab_area to 0
    if(value == 'G + 1'){
        $('#sf_slab_area').val(0);
        $('#tf_slab_area').val(0);
    }else if(value = 'G + 2'){
        $('#tf_slab_area').val(0);
    }
}


function validateForm() {
  let x = document.forms["myForm"]
  let isValid = true;
  let no_of_floors = x["no_of_floors"].value ? x["no_of_floors"].value : '';
  let floor_options = ['G + 1','G + 2','G + 3','G + 4'];  
    for(let i=0; i<x.length; i++){
        switch(x[i].id){
            case("project_number"):
                if(x[i].value == ""){
                    document.getElementById("project_number_error").setAttribute("class", "error");
                    isValid = false;
                }
                else 
                 {
                      document.getElementById("project_number_error").setAttribute("class", "d-none");
                 }
                break;
            case("project_name"):
                if(x[i].value == ""){
                    document.getElementById("project_name_error").setAttribute("class", "error");
                    isValid = false;
                }
                else 
                 {
                      document.getElementById("project_name_error").setAttribute("class", "d-none");
                 }
                break;
            case("project_location"):
                 if(x[i].value == ""){
                    document.getElementById("project_location_error").setAttribute("class", "error");
                    isValid = false;
                 }
                else 
                    {
                        document.getElementById("project_location_error").setAttribute("class", "d-none");
                    }
                break;
            case("no_of_floors"):
                if(x[i].value == ""){
                    document.getElementById("no_of_floors_error").setAttribute("class", "error");
                    isValid = false;
                }
                else 
                    {
                        document.getElementById("no_of_floors_error").setAttribute("class", "d-none");
                    }
                break;
            case("package_type"):
                if(x[i].value == ""){
                    document.getElementById("package_type_error").setAttribute("class", "error");
                    isValid = false;
                }
                else 
                    {
                        document.getElementById("package_type_error").setAttribute("class", "d-none");
                    }
                break;
            case("date_of_initial_advance"):
                if(x[i].value == ""){
                    document.getElementById("date_of_initial_advance_error").setAttribute("class", "error");
                    isValid = false;
                }
                else 
                    {
                        document.getElementById("date_of_initial_advance_error").setAttribute("class", "d-none");
                    }
                break;
            case("date_of_agreement"):
                if(x[i].value == ""){
                    document.getElementById("date_of_agreement_error").setAttribute("class", "error");
                    isValid = false;
                }
                else 
                    {
                        document.getElementById("date_of_agreement_error").setAttribute("class", "d-none");
                    }
                break;
            case("sales_executive"):
                if(x[i].value == ""){
                    document.getElementById("sales_executive_error").setAttribute("class", "error");
                    isValid = false;
                }
                else 
                    {
                        document.getElementById("sales_executive_error").setAttribute("class", "d-none");
                    }
                break;
            case("site_area"):
                if(x[i].value == ""){
                    document.getElementById("site_area_error").setAttribute("class", "error");
                    isValid = false;
                }
                else 
                    {
                        document.getElementById("site_area_error").setAttribute("class", "d-none");
                    }
                break;
            case("paid_percentage"):
                if(x[i].value == ""){
                    document.getElementById("paid_percentage_error").setAttribute("class", "error");
                    isValid = false;
                }
                else 
                    {
                        document.getElementById("paid_percentage_error").setAttribute("class", "d-none");
                    }
                break;
            case("project_value"):
                if(x[i].value == ""){
                    document.getElementById("project_value_error").setAttribute("class", "error");
                    isValid = false;
                }
                else 
                    {
                        document.getElementById("project_value_error").setAttribute("class", "d-none");
                    }
                break;
            case("cost_sheet"):
                if(x[i].files.length == 0){
                    document.getElementById("cost_sheet_error").setAttribute("class", "error");
                    isValid = false;
                }
                else 
                    {
                        document.getElementById("cost_sheet_error").setAttribute("class", "d-none");
                    }
                break;
            case("site_inspection_report"):
                if(x[i].files.length == 0){
                    document.getElementById("site_inspection_report_error").setAttribute("class", "error");
                    isValid = false;
                }
                else 
                    {
                        document.getElementById("site_inspection_report_error").setAttribute("class", "d-none");
                    }
                break;
            case("shr_oht"):
                if(x[i].value == ""){
                    document.getElementById("shr_oht_error").setAttribute("class", "error");
                    isValid = false;
                }
                else 
                    {
                        document.getElementById("shr_oht_error").setAttribute("class", "d-none");
                    }
                break;
            case("gf_slab_area"):
                if(floor_options.includes(no_of_floors) && x[i].value == ""){
                    document.getElementById("gf_slab_area_error").setAttribute("class", "error");
                    isValid = false;
                }
                else
                    {
                        document.getElementById("gf_slab_area_error").setAttribute("class", "d-none");
                    }
                break;
            case("ff_slab_area"):
                if(floor_options.includes(no_of_floors) && x[i].value == ""){
                    document.getElementById("ff_slab_area_error").setAttribute("class", "error");
                    isValid = false;
                }
                else 
                    {
                        document.getElementById("ff_slab_area_error").setAttribute("class", "d-none");
                    }
                break;
            case("sf_slab_area"):
                if(floor_options.includes(no_of_floors) && x[i].value == ""){
                    document.getElementById("sf_slab_area_error").setAttribute("class", "error");
                    isValid = false;
                }
                else 
                    {
                        document.getElementById("sf_slab_area_error").setAttribute("class", "d-none");
                    }
                break;
            case("tf_slab_area"):
                if(floor_options.includes(no_of_floors) && x[i].value == ""){
                    document.getElementById("tf_slab_area_error").setAttribute("class", "error");
                    isValid = false;
                }
                else 
                    {
                        document.getElementById("tf_slab_area_error").setAttribute("class", "d-none");
                    }
                break;
                        
        }
        document.getElementById('create_project_submit').disabled=isValid;
    }
  return isValid;
}

