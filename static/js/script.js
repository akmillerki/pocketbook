$(document).ready(function() {
	// slider
	$('#coin-slider').coinslider({ 
		width: 584,
		height: 325,
		delay: 5000,
		opacity: 1
	});
	$('.coin-slider ').hover(function(){$('#cs-navigation-coin-slider a').fadeIn()},function(){$('#cs-navigation-coin-slider a').fadeOut()})
});