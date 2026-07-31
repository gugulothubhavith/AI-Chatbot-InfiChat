UPDATE subscription_plans SET limits = limits || '{"web_search_per_month": 5}'::jsonb WHERE name = 'Free';
UPDATE subscription_plans SET limits = limits || '{"web_search_per_month": 20}'::jsonb, price_annual = 1910 WHERE name = 'Starter';
UPDATE subscription_plans SET limits = limits || '{"web_search_per_month": 100}'::jsonb, price_annual = 4790 WHERE name = 'Pro';
UPDATE subscription_plans SET limits = limits || '{"web_search_per_month": 500}'::jsonb, price_annual = 9590 WHERE name = 'Max';
UPDATE subscription_plans SET limits = limits || '{"web_search_per_month": 999999}'::jsonb WHERE name = 'Enterprise';
