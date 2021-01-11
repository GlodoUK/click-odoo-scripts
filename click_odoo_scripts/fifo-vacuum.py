#!/usr/bin/env python


import logging

import click
import click_odoo

_logger = logging.getLogger(__name__)


@click.command()
@click_odoo.env_options(default_log_level="info")
def main(env):
    """
    Under 12.0 FIFO vacuum'ing only occurs in a limit number of scenarios. This
    results in a large amount of FIFO moves to be vacuumed when running the stock
    valuation report.

    On larger systems, where the stock valuation has not been run for a year, this
    can infact just not finish in a timely manner.

    This scripts splits the FIFO moves by product, rather than attempting to do
    them all in 1 go.
    """

    _logger.info("Start split FIFO vacuum")

    fifo_valued_products = env["product.product"]
    fifo_valued_products |= (
        env["product.template"]
        .search([("property_cost_method", "=", "fifo")])
        .mapped("product_variant_ids")
    )
    fifo_valued_categories = env["product.category"].search(
        [("property_cost_method", "=", "fifo")]
    )
    fifo_valued_products |= env["product.product"].search(
        [("categ_id", "child_of", fifo_valued_categories.ids)]
    )
    # Vanilla until here
    for product in fifo_valued_products:
        print(product)
        moves_to_vacuum = env["stock.move"].search(
            [("product_id", "in", product.ids), ("remaining_qty", "<", 0)]
            + env["stock.move"]._get_all_base_domain()
        )
        if moves_to_vacuum:
            moves_to_vacuum._fifo_vacuum()
            env.cr.commit()


if __name__ == "__main__":
    main()
