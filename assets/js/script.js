// App initialization code goes here

$(function () {
  $('body').on('click', 'button.add-evidence', function () {
    var $this = $(this)
    var $newEvidence = $('<div class="form-group"><div class="input-group"><input type="url" class="form-control" id="#" placeholder="http://..."><span class="input-group-btn"><button class="btn btn-primary add-evidence" type="button">+</button></span></div></div>')
    $this.removeClass('add-evidence btn-primary').addClass('rm-evidence btn-danger').text('-')
    var $evidenceInputs = $this.closest('.evidence-inputs')

    var count = $evidenceInputs.data('counter')
    count = count + 1
    $evidenceInputs.data('counter', count)

    var evidenceId = $evidenceInputs.attr('id')
    $newEvidence.find('.form-control').attr('id', evidenceId + '-' + count)
    $evidenceInputs.append($newEvidence)
  })

  $('body').on('click', 'button.rm-evidence', function () {
    var $this = $(this)
    $this.closest('.form-group').remove()
  })
})
