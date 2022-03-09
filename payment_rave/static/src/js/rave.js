/* global Rave */
odoo.define("payment_rave.payment_form", (require) => {
  "use strict";

  const checkoutForm = require("payment.checkout_form");
  const manageForm = require("payment.manage_form");

  const raveMixin = {
    /**
     * Redirect the customer to Flutterwave hosted payment page.
     *
     * @override method from payment.payment_form_mixin
     * @private
     * @param {string} provider - The provider of the payment option's acquirer
     * @param {number} paymentOptionId - The id of the payment option handling the transaction
     * @param {object} processingValues - The processing values of the transaction
     * @return {undefined}
     */
    _processRedirectPayment: function (
      provider,
      paymentOptionId,
      processingValues
    ) {
      if (provider !== "rave") {
        return this._super(...arguments);
      }

      console.log(processingValues);

      // const stripeJS = Stripe(processingValues['publishable_key'],
      //     this._prepareStripeOptions(processingValues));
      // stripeJS.redirectToCheckout({
      //     sessionId: processingValues['session_id']
      // });

      alert("redirected to checkout page");
    },

    /**
     * Prepare the options to init the Stripe JS Object
     *
     * Function overriden in internal module
     *
     * @param {object} processingValues
     * @return {object}
     */
    _prepareRaveOptions: function (processingValues) {
      return {};
    },
  };

  checkoutForm.include(raveMixin);
  manageForm.include(raveMixin);
});
