from unit_economic.models import MarketplaceCommission, MarketplaceLogistic


def wadd_marketplace_comission_to_db(
    product_obj,
    fbs_commission=None,
    fbo_commission=None,
    dbs_commission=None,
    fbs_express_commission=None,
):
    """
    Записывает комиссии маркетплейсов в базу данных
    """
    search_params = {"marketplace_product": product_obj}
    values_for_update = {
        "fbs_commission": fbs_commission,
        "fbo_commission": fbo_commission,
        "dbs_commission": dbs_commission,
        "fbs_express_commission": fbs_express_commission,
    }

    MarketplaceCommission.objects.update_or_create(
        defaults=values_for_update, **search_params
    )


def add_marketplace_logistic_to_db(
    product_obj,
    cost_logistic=None,
    cost_logistic_fbo=None,
    cost_logistic_fbs=None,
):
    """
    Записывает затраты на логистику маркетплейсов в базу данных
    """
    search_params = {"marketplace_product": product_obj}
    values_for_update = {
        "cost_logistic": cost_logistic,
        "cost_logistic_fbo": cost_logistic_fbo,
        "cost_logistic_fbs": cost_logistic_fbs,
    }
    MarketplaceLogistic.objects.update_or_create(
        defaults=values_for_update, **search_params
    )
