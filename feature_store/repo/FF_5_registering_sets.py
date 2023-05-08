import FF_4_transformations as transformations


def register_sets(ff):
    # Register the training set
    ff.register_training_set(
        name="training_features",
        variant="default",
        features=[
            ("lag_1_vaccine_interest"),
            ("lag_2_vaccine_interest"),
            ("lag_1_vaccine_intent"),
            ("lag_2_vaccine_intent"),
            ("lag_1_vaccine_safety"),
            ("lag_2_vaccine_safety"),
            ("lag_1_weekly_vaccinations_count"),
            ("lag_2_weekly_vaccinations_count"),
        ],
        labels=[
            ("weekly_vaccinations_count"),
        ],
    )

    # TODO: There's got to be a way better way to do this
    ff.register_training_set(
        name="serving_features",
        variant="default",
        features=[
            ("lag_1_vaccine_interest"),
            ("lag_2_vaccine_interest"),
            ("lag_1_vaccine_intent"),
            ("lag_2_vaccine_intent"),
            ("lag_1_vaccine_safety"),
            ("lag_2_vaccine_safety"),
            ("lag_1_weekly_vaccinations_count"),
            ("lag_2_weekly_vaccinations_count"),
        ],
    )
