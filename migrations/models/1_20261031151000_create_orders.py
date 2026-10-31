from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `orders` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `order_number` VARCHAR(32) NOT NULL UNIQUE COMMENT '订单号',
    `user_id` INT NOT NULL COMMENT '所属用户id',
    `total_amount` DECIMAL(10,2) NOT NULL COMMENT '订单金额',
    `status` VARCHAR(20) NOT NULL COMMENT '订单状态' DEFAULT '待处理',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL COMMENT '更新时间' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    KEY `idx_orders_user_id_f00b6a` (`user_id`),
    KEY `idx_orders_user_id_09581a` (`user_id`, `status`)
) CHARACTER SET utf8mb4 COMMENT='订单表';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `orders`;"""
