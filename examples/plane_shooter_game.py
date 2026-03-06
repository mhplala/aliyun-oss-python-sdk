"""一个简易的打飞机游戏（Tkinter 版本）。

运行方式：
    python examples/plane_shooter_game.py

操作说明：
- 左右方向键 / A、D：移动战机
- 空格：发射子弹
- R：游戏结束后重新开始
"""

from __future__ import annotations

import random
import tkinter as tk


WIDTH = 480
HEIGHT = 700
PLAYER_WIDTH = 48
PLAYER_HEIGHT = 56
ENEMY_WIDTH = 44
ENEMY_HEIGHT = 40
BULLET_WIDTH = 6
BULLET_HEIGHT = 14
PLAYER_SPEED = 22
BULLET_SPEED = 18
ENEMY_SPEED_BASE = 4
ENEMY_SPAWN_EVERY_MS = 550
GAME_TICK_MS = 16


class PlaneShooterGame:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("打飞机小游戏")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#0a1a2a", highlightthickness=0)
        self.canvas.pack()

        self.score = 0
        self.level = 1
        self.game_over = False

        self.player = self._create_player()
        self.bullets: list[int] = []
        self.enemies: list[int] = []

        self.score_text = self.canvas.create_text(
            10,
            10,
            anchor="nw",
            text="分数: 0  等级: 1",
            fill="#f5f6fa",
            font=("Helvetica", 14, "bold"),
        )

        self.tip_text = self.canvas.create_text(
            WIDTH // 2,
            HEIGHT // 2,
            text="←/→ 或 A/D 移动，空格发射",
            fill="#dfe6e9",
            font=("Helvetica", 16, "bold"),
        )
        self.root.after(1800, lambda: self.canvas.itemconfigure(self.tip_text, state="hidden"))

        self.root.bind("<Left>", lambda event: self.move_player(-1))
        self.root.bind("<Right>", lambda event: self.move_player(1))
        self.root.bind("<a>", lambda event: self.move_player(-1))
        self.root.bind("<d>", lambda event: self.move_player(1))
        self.root.bind("<space>", lambda event: self.shoot())
        self.root.bind("<r>", lambda event: self.restart())

        self._spawn_loop()
        self._game_loop()

    def _create_player(self) -> int:
        x = WIDTH // 2
        y = HEIGHT - 80
        return self.canvas.create_polygon(
            x,
            y - PLAYER_HEIGHT // 2,
            x - PLAYER_WIDTH // 2,
            y + PLAYER_HEIGHT // 2,
            x,
            y + PLAYER_HEIGHT // 4,
            x + PLAYER_WIDTH // 2,
            y + PLAYER_HEIGHT // 2,
            fill="#74b9ff",
            outline="#dff9fb",
            width=2,
        )

    def move_player(self, direction: int) -> None:
        if self.game_over:
            return
        x1, _, x2, _ = self.canvas.bbox(self.player)
        move_x = direction * PLAYER_SPEED

        if x1 + move_x < 0:
            move_x = -x1
        elif x2 + move_x > WIDTH:
            move_x = WIDTH - x2

        self.canvas.move(self.player, move_x, 0)

    def shoot(self) -> None:
        if self.game_over:
            return
        x1, y1, x2, _ = self.canvas.bbox(self.player)
        bullet_x = (x1 + x2) / 2
        bullet = self.canvas.create_rectangle(
            bullet_x - BULLET_WIDTH // 2,
            y1 - BULLET_HEIGHT,
            bullet_x + BULLET_WIDTH // 2,
            y1,
            fill="#ffeaa7",
            outline="",
        )
        self.bullets.append(bullet)

    def _spawn_enemy(self) -> None:
        spawn_x = random.randint(ENEMY_WIDTH // 2 + 4, WIDTH - ENEMY_WIDTH // 2 - 4)
        enemy = self.canvas.create_oval(
            spawn_x - ENEMY_WIDTH // 2,
            -ENEMY_HEIGHT,
            spawn_x + ENEMY_WIDTH // 2,
            0,
            fill="#ff7675",
            outline="#fab1a0",
            width=2,
        )
        self.enemies.append(enemy)

    def _spawn_loop(self) -> None:
        if not self.game_over:
            self._spawn_enemy()
            self.root.after(ENEMY_SPAWN_EVERY_MS, self._spawn_loop)

    def _rect_overlap(self, id1: int, id2: int) -> bool:
        ax1, ay1, ax2, ay2 = self.canvas.bbox(id1)
        bx1, by1, bx2, by2 = self.canvas.bbox(id2)
        return ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1

    def _update_level(self) -> None:
        self.level = self.score // 10 + 1

    def _update_hud(self) -> None:
        self.canvas.itemconfigure(self.score_text, text=f"分数: {self.score}  等级: {self.level}")

    def _explode_enemy(self, enemy: int) -> None:
        x1, y1, x2, y2 = self.canvas.bbox(enemy)
        self.canvas.delete(enemy)
        if enemy in self.enemies:
            self.enemies.remove(enemy)
        blast = self.canvas.create_oval(x1 - 8, y1 - 8, x2 + 8, y2 + 8, fill="#fdcb6e", outline="")
        self.root.after(90, lambda: self.canvas.delete(blast))

    def _game_loop(self) -> None:
        if self.game_over:
            return

        # 子弹移动
        for bullet in self.bullets[:]:
            self.canvas.move(bullet, 0, -BULLET_SPEED)
            _, y1, _, _ = self.canvas.bbox(bullet)
            if y1 < -BULLET_HEIGHT:
                self.canvas.delete(bullet)
                self.bullets.remove(bullet)

        # 敌机移动
        enemy_speed = ENEMY_SPEED_BASE + self.level
        for enemy in self.enemies[:]:
            self.canvas.move(enemy, 0, enemy_speed)
            _, _, _, y2 = self.canvas.bbox(enemy)
            if y2 > HEIGHT + ENEMY_HEIGHT:
                self.canvas.delete(enemy)
                self.enemies.remove(enemy)

        # 碰撞检测：子弹 vs 敌机
        for bullet in self.bullets[:]:
            hit_enemy = None
            for enemy in self.enemies:
                if self._rect_overlap(bullet, enemy):
                    hit_enemy = enemy
                    break
            if hit_enemy is not None:
                self.canvas.delete(bullet)
                self.bullets.remove(bullet)
                self._explode_enemy(hit_enemy)
                self.score += 1
                self._update_level()
                self._update_hud()

        # 碰撞检测：敌机 vs 玩家
        for enemy in self.enemies:
            if self._rect_overlap(enemy, self.player):
                self._on_game_over()
                return

        self.root.after(GAME_TICK_MS, self._game_loop)

    def _on_game_over(self) -> None:
        self.game_over = True
        self.canvas.create_text(
            WIDTH // 2,
            HEIGHT // 2 - 20,
            text="游戏结束",
            fill="#ffcccc",
            font=("Helvetica", 34, "bold"),
        )
        self.canvas.create_text(
            WIDTH // 2,
            HEIGHT // 2 + 26,
            text="按 R 重新开始",
            fill="#f8f8f8",
            font=("Helvetica", 18),
        )

    def restart(self) -> None:
        if not self.game_over:
            return

        self.canvas.delete("all")
        self.score = 0
        self.level = 1
        self.game_over = False

        self.player = self._create_player()
        self.bullets.clear()
        self.enemies.clear()

        self.score_text = self.canvas.create_text(
            10,
            10,
            anchor="nw",
            text="分数: 0  等级: 1",
            fill="#f5f6fa",
            font=("Helvetica", 14, "bold"),
        )
        self.tip_text = self.canvas.create_text(
            WIDTH // 2,
            HEIGHT // 2,
            text="←/→ 或 A/D 移动，空格发射",
            fill="#dfe6e9",
            font=("Helvetica", 16, "bold"),
        )
        self.root.after(1200, lambda: self.canvas.itemconfigure(self.tip_text, state="hidden"))

        self._spawn_loop()
        self._game_loop()


def main() -> None:
    root = tk.Tk()
    PlaneShooterGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
