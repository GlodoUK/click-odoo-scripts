#!/usr/bin/env python
import logging

import click
import click_odoo

_logger = logging.getLogger(__name__)


@click.command()
@click_odoo.env_options(default_log_level="info")
def main(env):
    """
    Fix up script for 12.0 where stock.quants and stock.moves can become out of
    sync. This is a workaround until we can find the ultimate cause.

    To execute: `./click-odoo-fix-quants.py -d DBNAME here`

    This will work through all mangled quants and fix them all until it finishes.
    On a large system, you want to run this at a lower traffic period of time ideally.

    This click-odoo script is based on an Odoo support ticket.
    """

    _logger.info("Finding quants")
    quants = env["stock.quant"].sudo().search([])
    move_line_ids = []
    move_line_ids_touched = []
    for quant in quants:
        _logger.info("Working on %s", quant)

        move_lines = (
            env["stock.move.line"]
            .sudo()
            .search(
                [
                    ("product_id", "=", quant.product_id.id),
                    ("location_id", "=", quant.location_id.id),
                    ("lot_id", "=", quant.lot_id.id),
                    ("package_id", "=", quant.package_id.id),
                    ("owner_id", "=", quant.owner_id.id),
                    ("product_qty", "!=", 0),
                ]
            )
        )
        move_line_ids += move_lines.ids
        reserved_on_move_lines = sum(move_lines.mapped("product_qty"))
        if quant.location_id.should_bypass_reservation():
            # If a quant is in a location that should bypass the reservation,
            # its `reserved_quantity` field should be 0.
            if quant.reserved_quantity != 0:
                quant.write({"reserved_quantity": 0})
        else:
            # If a quant is in a reservable location, its `reserved_quantity`
            # should be exactly the sum of the `product_qty` of all the
            # partially_available / assigned move lines with the same
            # characteristics.
            if quant.reserved_quantity == 0:
                if move_lines:
                    move_lines.with_context(bypass_reservation_update=True).write(
                        {"product_uom_qty": 0}
                    )
                    move_line_ids_touched += move_lines.ids
            elif quant.reserved_quantity < 0:
                quant.write({"reserved_quantity": 0})
                if move_lines:
                    move_lines.with_context(bypass_reservation_update=True).write(
                        {"product_uom_qty": 0}
                    )
                    move_line_ids_touched += move_lines.ids
            else:
                if reserved_on_move_lines != quant.reserved_quantity:
                    move_lines.with_context(bypass_reservation_update=True).write(
                        {"product_uom_qty": 0}
                    )
                    quant.write({"reserved_quantity": 0})
                    move_line_ids_touched += move_lines.ids
                else:
                    if any(move_line.product_qty < 0 for move_line in move_lines):
                        move_lines.with_context(bypass_reservation_update=True).write(
                            {"product_uom_qty": 0}
                        )
                        quant.write({"reserved_quantity": 0})
                        move_line_ids_touched += move_lines.ids

    _logger.info("Finding mangled stock.move.lines")
    move_lines = (
        env["stock.move.line"]
        .sudo()
        .search(
            [
                ("product_id.type", "=", "product"),
                ("product_qty", "!=", 0),
                ("id", "not in", move_line_ids),
            ]
        )
    )
    move_lines_to_unreserve = []
    for move_line in move_lines:
        if not move_line.location_id.should_bypass_reservation():
            move_lines_to_unreserve.append(move_line.id)
    if len(move_lines_to_unreserve) > 1:
        _logger.info(
            "Manually unreserving stock.move.line's %s", move_lines_to_unreserve
        )
        env.cr.execute(
            """
            UPDATE
                stock_move_line
            SET
                product_uom_qty = 0, product_qty = 0
            WHERE
                id in %s ;
            """
            % (tuple(move_lines_to_unreserve),)
        )
    elif len(move_lines_to_unreserve) == 1:
        _logger.info(
            "Manually unreserving stock.move.line's %s", move_lines_to_unreserve
        )
        env.cr.execute(
            """
            UPDATE
                stock_move_line
            SET
                product_uom_qty = 0, product_qty = 0
            WHERE
                id = %s ;
            """
            % (move_lines_to_unreserve[0])
        )
    _logger.info("Invalidating ORM cache")
    env.cache.invalidate()
    _logger.info("Recomputing mangled stock.move states")
    env["stock.move.line"].sudo().browse(move_lines_to_unreserve).mapped(
        "move_id"
    )._recompute_state()
    _logger.info("Recomputing unreserved stock.move states")
    env["stock.move.line"].sudo().browse(move_line_ids_touched).mapped(
        "move_id"
    )._recompute_state()


if __name__ == "__main__":
    main()
