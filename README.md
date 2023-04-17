<p align="center">
    <img title="Flutterwave" height="200" src="https://flutterwave.com/images/logo/full.svg" width="50%"/>
</p>

# Flutterwave Odoo (v14).

This Flutterwave Odoo Package provides easy access to Flutterwave for Business (F4B) v3 APIs on odoo. It abstracts the complexity involved in direct integration and allows you to make quick calls to the APIs.

Available features include:

- Collections: Card, Account, Mobile money, Bank Transfers, USSD, Barter, NQR.

## Table of Contents
1. [Requirements](#requirements)
2. [Installation](#installation)
3. [Usage](#usage)
4. [Testing](#testing)
5. [Debugging Errors](#debugging-errors)
6. [Support](#support)
7. [Contribution guidelines](#contribution-guidelines)
8. [License](#license)
9. [Changelog](#changelog)
10. [Development] (#development)

<a id="requirements"></a>

## Requirements

1. Flutterwave for business [API Keys](https://developer.flutterwave.com/docs/integration-guides/authentication)
2. Acceptable Odoo version: 14 Only


<a id="installation"></a>

## Installation

This addon can be installed as any other regular Odoo addon:

- Unzip the addon in one of Odoo's addons paths.
- Login to Odoo as a user with administrative privileges, go into debug mode.
- Go to *Apps -> Update Apps List*, click *Update* in the dialog window.
- Go to *Apps -> Apps*, remove the *Apps* filter in the search bar and search
  for *Rave Payment Acquirer*. Click *Install* button on the addon.


## Usage

Now, let's configure the payment acquirer:

- Login to Odoo as a user with administrative privileges, go into debug mode.
- Go to *Website -> Configuration -> eCommerce -> Payment Acquirers* or
  *Invoicing -> Configuration -> Payments -> Payment Acquirers* and click
  *Configure* on the *Rave* acquirer.

- In the *Credentials* tab, enter the Public and Secret key from Rave 
  *API credentials* section noted earlier:

  - If necessary, you may change the forced payment type (eg. *Bank Link*, *Bank
  Transfer* or *Credit Card*), default rave widget language
  and the market country for your eCommerce shop.

- Click on the *Save* button.
- Click on the *Publish* button to make the acquirer available for you in the
  eCommerce shop.

<a id="development"></a>

## Development

To Test to application environment, you may choose to use docker. a suggestion would be to use the offical [odoo docker image](https://hub.docker.com/_/odoo).

There you would find a sample of a `docker-compose.yml` file if you prefer to use `docker-compose`.

To add the module to the odoo container addons simply mount the location of the module to `mnt\extra-addons` like in the sample below.

```docker-composer.yml

version: '3.1'
services:
  web:
    image: odoo:14.0
    depends_on:
      - db
    ports:
      - "8069:8069"
    volumes:
      - odoo-web-data:/var/lib/odoo
      - ../:/mnt/extra-addons
  db:
    image: postgres:13
    user: root
    environment:
      - POSTGRES_PASSWORD=odoo
      - POSTGRES_USER=odoo
      - POSTGRES_DB=postgres
    restart: always             # run as a service
    volumes:
        - ./postgresql:/var/lib/postgresql/data
  adminer:
    image: adminer
    restart: always
    ports:
      - 8066:8080

volumes:
  odoo-web-data:
  odoo-db-data:


```

<a id="debugging errors"></a>

## Debugging Errors
We understand that you may run into some errors while integrating our library. You can read more about our error messages [here](https://developer.flutterwave.com/docs/integration-guides/errors).

For `authorization` and `validation` error responses, double-check your API keys and request. If you get a `server` error, kindly engage the team for support.


<a id="support"></a>

## Support
For additional assistance using this library, contact the developer experience (DX) team via [email](mailto:developers@flutterwavego.com) or on [slack](https://bit.ly/34Vkzcg).

You can also follow us [@FlutterwaveEng](https://twitter.com/FlutterwaveEng) and let us know what you think 😊.


<a id="contribution-guidelines"></a>

## Contribution guidelines
Read more about our community contribution guidelines [here](/CONTRIBUTING.md)


<a id="license"></a>

## License

By contributing to this library, you agree that your contributions will be licensed under its [MIT license](/LICENSE).

Copyright (c) Flutterwave Inc.

<a id="references"></a>

## Flutterwave API  References

- [Flutterwave API Documentation](https://developer.flutterwave.com)
- [Flutterwave Dashboard](https://app.flutterwave.com)  