import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Chess } from 'chess.js';
import { Chessboard } from 'react-chessboard';
import {
  Activity,
  BadgeHelp,
  Brain,
  Crown,
  Flag,
  Gauge,
  History,
  Loader2,
  Play,
  RefreshCcw,
  RotateCcw,
  Shield,
  Sparkles,
  Swords,
  Timer,
  Wifi,
  WifiOff,
} from 'lucide-react';

const API_BASE = 'http://localhost:8001';
const WS_BASE = 'ws://localhost:8001';
const START_FEN = new Chess().fen();
const PROMOTION_PIECES = [
  { value: 'q', label: 'Queen' },
  { value: 'r', label: 'Rook' },
  { value: 'b', label: 'Bishop' },
  { value: 'n', label: 'Knight' },
];

const PIECE_VALUES = { p: 1, n: 3, b: 3, r: 5, q: 9 };

function moveFromUci(uci) {
  if (!uci || uci.length < 4) return null;
  return {
    from: uci.slice(0, 2),
    to: uci.slice(2, 4),
    promotion: uci[4],
  };
}

function formatTime(ms) {
  if (ms < 1000) return `${ms} ms`;
  const seconds = ms / 1000;
  return `${Number.isInteger(seconds) ? seconds : seconds.toFixed(1)} s`;
}

function getCapturedPieces(fen) {
  const board = new Chess(fen).board().flat();
  const remaining = { w: {}, b: {} };

  for (const square of board) {
    if (!square) continue;
    remaining[square.color][square.type] = (remaining[square.color][square.type] || 0) + 1;
  }

  const starting = { p: 8, n: 2, b: 2, r: 2, q: 1 };
  return {
    white: Object.entries(starting).flatMap(([piece, count]) =>
      Array(Math.max(0, count - (remaining.w[piece] || 0))).fill(piece),
    ),
    black: Object.entries(starting).flatMap(([piece, count]) =>
      Array(Math.max(0, count - (remaining.b[piece] || 0))).fill(piece),
    ),
  };
}

function capturedMaterial(captured) {
  return captured.reduce((sum, piece) => sum + (PIECE_VALUES[piece] || 0), 0);
}

export default function App() {
  const [game, setGame] = useState(() => new Chess());
  const [fen, setFen] = useState(START_FEN);
  const [gameId, setGameId] = useState(null);
  const [moveHistory, setMoveHistory] = useState([]);
  const [lastMove, setLastMove] = useState(null);
  const [selectedSquare, setSelectedSquare] = useState(null);
  const [pendingPromotion, setPendingPromotion] = useState(null);

  const [humanColor, setHumanColor] = useState('white');
  const [boardOrientation, setBoardOrientation] = useState('white');
  const [thinkTime, setThinkTime] = useState(1000);
  const [depth, setDepth] = useState('');
  const [skillLevel, setSkillLevel] = useState(20);

  const [isConnected, setIsConnected] = useState(false);
  const [connectionText, setConnectionText] = useState('Checking engine server');
  const [isStarting, setIsStarting] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [score, setScore] = useState(0);
  const [currentDepth, setCurrentDepth] = useState(0);
  const [notice, setNotice] = useState('');

  const [showModal, setShowModal] = useState(false);
  const [gameOverInfo, setGameOverInfo] = useState({ result: '', reason: '' });

  const wsRef = useRef(null);
  const gameRef = useRef(new Chess());
  const moveHistoryEndRef = useRef(null);
  const noticeTimerRef = useRef(null);

  const isHumanTurn = useMemo(() => {
    const turn = game.turn() === 'w' ? 'white' : 'black';
    return gameId && !showModal && !isThinking && turn === humanColor;
  }, [game, gameId, humanColor, isThinking, showModal]);

  const legalTargets = useMemo(() => {
    if (!selectedSquare || !isHumanTurn) return [];
    return game.moves({ square: selectedSquare, verbose: true }).map((move) => move.to);
  }, [game, isHumanTurn, selectedSquare]);

  const movePairs = useMemo(() => {
    const pairs = [];
    for (let i = 0; i < moveHistory.length; i += 2) {
      pairs.push({
        num: Math.floor(i / 2) + 1,
        white: moveHistory[i],
        black: moveHistory[i + 1],
      });
    }
    return pairs;
  }, [moveHistory]);

  const captured = useMemo(() => getCapturedPieces(fen), [fen]);
  const materialDiff = capturedMaterial(captured.black) - capturedMaterial(captured.white);

  const syncGame = useCallback((nextGame, options = {}) => {
    const synced = new Chess(nextGame.fen());
    gameRef.current = synced;
    setGame(synced);
    setFen(synced.fen());
    if (options.lastMove !== undefined) setLastMove(options.lastMove);
    setSelectedSquare(null);
  }, []);

  const showNotice = useCallback((message) => {
    setNotice(message);
    window.clearTimeout(noticeTimerRef.current);
    noticeTimerRef.current = window.setTimeout(() => setNotice(''), 3200);
  }, []);

  useEffect(() => {
    let cancelled = false;
    const checkHealth = async () => {
      try {
        const response = await fetch(`${API_BASE}/health`);
        if (!response.ok) throw new Error('health check failed');
        if (!cancelled) {
          setIsConnected(true);
          setConnectionText('Engine server online');
        }
      } catch {
        if (!cancelled) {
          setIsConnected(false);
          setConnectionText('Engine server offline');
        }
      }
    };

    checkHealth();
    const intervalId = window.setInterval(checkHealth, 5000);
    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
      window.clearTimeout(noticeTimerRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [showNotice]);

  useEffect(() => {
    moveHistoryEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, [moveHistory]);

  const appendMove = useCallback((move) => {
    if (!move?.san) return;
    setMoveHistory((moves) => [...moves, move.san]);
    setLastMove({ from: move.from, to: move.to, san: move.san });
  }, []);

  const applyBackendFen = useCallback(
    (backendFen) => {
      if (!backendFen) return;
      const nextGame = new Chess(backendFen);
      syncGame(nextGame);
    },
    [syncGame],
  );

  const applyMoveToLocalGame = useCallback(
    (moveLike) => {
      const nextGame = new Chess(gameRef.current.fen());
      const move = nextGame.move(moveLike);
      if (!move) return null;
      gameRef.current = nextGame;
      setGame(nextGame);
      setFen(nextGame.fen());
      appendMove(move);
      setSelectedSquare(null);
      return move;
    },
    [appendMove],
  );

  const connectWebSocket = useCallback(
    (id) => {
      const ws = new WebSocket(`${WS_BASE}/games/${id}/live`);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        setConnectionText('Live engine link active');
      };

      ws.onclose = () => {
        setIsConnected(false);
        setConnectionText('Live link closed');
        setIsThinking(false);
      };

      ws.onerror = () => {
        showNotice('The live engine connection hit an error.');
      };

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);

        if (msg.type === 'state') {
          applyBackendFen(msg.fen);
          return;
        }

        if (msg.type === 'human_move') {
          applyBackendFen(msg.fen);
          return;
        }

        if (msg.type === 'thinking') {
          setIsThinking(true);
          if (msg.score_cp !== undefined && msg.score_cp !== null) setScore(msg.score_cp);
          if (msg.depth) setCurrentDepth(msg.depth);
          return;
        }

        if (msg.type === 'engine_move') {
          setIsThinking(false);
          const moveObj = moveFromUci(msg.move);
          if (moveObj) {
            try {
              applyMoveToLocalGame(moveObj);
            } catch {
              applyBackendFen(msg.fen);
            }
          } else {
            applyBackendFen(msg.fen);
          }
          return;
        }

        if (msg.type === 'game_over') {
          setIsThinking(false);
          setGameOverInfo({ result: msg.result || '1/2-1/2', reason: msg.reason || 'completed' });
          setShowModal(true);
          return;
        }

        if (msg.type === 'error') {
          setIsThinking(false);
          showNotice(`Engine error: ${msg.detail}`);
        }
      };
    },
    [applyBackendFen, applyMoveToLocalGame, showNotice],
  );

  const startNewGame = useCallback(
    async (playerColor = humanColor) => {
      setIsStarting(true);
      setNotice('');

      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }

      const newGame = new Chess();
      gameRef.current = newGame;
      setGame(newGame);
      setFen(newGame.fen());
      setMoveHistory([]);
      setLastMove(null);
      setSelectedSquare(null);
      setPendingPromotion(null);
      setScore(0);
      setCurrentDepth(0);
      setIsThinking(false);
      setShowModal(false);
      setHumanColor(playerColor);
      setBoardOrientation(playerColor);

      try {
        const response = await fetch(`${API_BASE}/games`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            human_color: playerColor,
            skill_level: skillLevel,
            think_time_ms: thinkTime,
            depth: depth ? Number(depth) : null,
          }),
        });

        if (!response.ok) throw new Error('Failed to create session');

        const data = await response.json();
        setGameId(data.game_id);

        if (playerColor === 'black' && data.engine_move) {
          const engineOpening = moveFromUci(data.engine_move);
          if (engineOpening) applyMoveToLocalGame(engineOpening);
          else applyBackendFen(data.fen);
        } else {
          applyBackendFen(data.fen);
        }

        connectWebSocket(data.game_id);
      } catch {
        setGameId(null);
        setIsConnected(false);
        setConnectionText('Engine server unavailable');
        showNotice('Could not start a match. Make sure the backend is running on port 8001.');
      } finally {
        setIsStarting(false);
      }
    },
    [
      applyBackendFen,
      applyMoveToLocalGame,
      connectWebSocket,
      depth,
      humanColor,
      skillLevel,
      showNotice,
      thinkTime,
    ],
  );

  const moveIsPromotion = useCallback((from, to) => {
    const piece = gameRef.current.get(from);
    return piece?.type === 'p' && (to.endsWith('8') || to.endsWith('1'));
  }, []);

  const submitMove = useCallback(
    (moveObj) => {
      if (!gameId || !isHumanTurn) return false;

      try {
        const move = applyMoveToLocalGame(moveObj);
        if (!move) return false;

        if (wsRef.current?.readyState === WebSocket.OPEN) {
          setIsThinking(true);
          wsRef.current.send(JSON.stringify({ type: 'move', move: move.lan || move.after }));
        } else {
          showNotice('Live connection is not ready. Reconnect by starting a new game.');
        }
        return true;
      } catch {
        return false;
      }
    },
    [applyMoveToLocalGame, gameId, isHumanTurn, showNotice],
  );

  const onDrop = useCallback(
    ({ sourceSquare, targetSquare }) => {
      if (!targetSquare || !isHumanTurn) return false;
      if (moveIsPromotion(sourceSquare, targetSquare)) {
        setPendingPromotion({ from: sourceSquare, to: targetSquare });
        return false;
      }
      return submitMove({ from: sourceSquare, to: targetSquare });
    },
    [isHumanTurn, moveIsPromotion, submitMove],
  );

  const onSquareClick = useCallback(
    ({ square }) => {
      if (!isHumanTurn) return;
      const piece = game.get(square);

      if (selectedSquare && legalTargets.includes(square)) {
        if (moveIsPromotion(selectedSquare, square)) {
          setPendingPromotion({ from: selectedSquare, to: square });
        } else {
          submitMove({ from: selectedSquare, to: square });
        }
        return;
      }

      if (piece && piece.color === (humanColor === 'white' ? 'w' : 'b')) {
        setSelectedSquare(square);
      } else {
        setSelectedSquare(null);
      }
    },
    [game, humanColor, isHumanTurn, legalTargets, moveIsPromotion, selectedSquare, submitMove],
  );

  const canDragPiece = useCallback(
    ({ square }) => {
      if (!square || !isHumanTurn) return false;
      const piece = game.get(square);
      return Boolean(piece && piece.color === (humanColor === 'white' ? 'w' : 'b'));
    },
    [game, humanColor, isHumanTurn],
  );

  const resignGame = useCallback(async () => {
    if (!gameId) return;
    setIsThinking(false);
    try {
      await fetch(`${API_BASE}/games/${gameId}`, { method: 'DELETE' });
    } catch {
      showNotice('Could not notify the backend, but the local game was ended.');
    }
    wsRef.current?.close();
    setGameOverInfo({
      result: humanColor === 'white' ? '0-1' : '1-0',
      reason: 'resignation',
    });
    setShowModal(true);
  }, [gameId, humanColor, showNotice]);

  const resetToSettings = useCallback(() => {
    wsRef.current?.close();
    setGameId(null);
    setShowModal(false);
    setIsThinking(false);
    setSelectedSquare(null);
    setPendingPromotion(null);
  }, []);

  const getScoreDisplay = () => {
    if (Math.abs(score) > 9000) return score > 0 ? 'Mate +' : 'Mate -';
    const pawns = score / 100;
    return pawns > 0 ? `+${pawns.toFixed(2)}` : pawns.toFixed(2);
  };

  const getEvalHeight = () => {
    const pawns = Math.max(-8, Math.min(8, score / 100));
    return ((pawns + 8) / 16) * 100;
  };

  const squareStyles = useMemo(() => {
    const styles = {};
    if (lastMove?.from) styles[lastMove.from] = { boxShadow: 'inset 0 0 0 999px rgba(233, 196, 106, 0.34)' };
    if (lastMove?.to) styles[lastMove.to] = { boxShadow: 'inset 0 0 0 999px rgba(233, 196, 106, 0.46)' };
    if (selectedSquare) styles[selectedSquare] = { boxShadow: 'inset 0 0 0 4px rgba(72, 187, 120, 0.95)' };
    for (const target of legalTargets) {
      styles[target] = {
        ...styles[target],
        backgroundImage: 'radial-gradient(circle, rgba(18, 24, 38, 0.34) 19%, transparent 20%)',
      };
    }
    return styles;
  }, [lastMove, legalTargets, selectedSquare]);

  const currentTurn = game.turn() === 'w' ? 'White' : 'Black';
  const statusText = !gameId
    ? 'Configure a match'
    : isThinking
      ? 'Engine searching'
      : isHumanTurn
        ? 'Your move'
        : `${currentTurn} to move`;

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <div className="brand-mark"><Crown size={22} /></div>
          <div>
            <h1>Chaturanga</h1>
            <span>Python chess engine</span>
          </div>
        </div>
        <div className={`connection-pill ${isConnected ? 'online' : 'offline'}`}>
          {isConnected ? <Wifi size={16} /> : <WifiOff size={16} />}
          <span>{connectionText}</span>
        </div>
      </header>

      {notice && <div className="toast" role="status">{notice}</div>}

      <main className="workspace">
        <section className="board-zone" aria-label="Chess board">
          <div className="player-strip">
            <div>
              <span className="player-label">{humanColor === 'white' ? 'Engine' : 'You'}</span>
              <strong>{humanColor === 'white' ? 'Black' : 'White'}</strong>
            </div>
            <CapturedRow pieces={humanColor === 'white' ? captured.white : captured.black} />
          </div>

          <div className="board-frame">
            <div className="eval-rail" aria-label={`Evaluation ${getScoreDisplay()}`}>
              <div className="eval-black" style={{ height: `${100 - getEvalHeight()}%` }} />
              <div className="eval-white" style={{ height: `${getEvalHeight()}%` }} />
              <span>{getScoreDisplay()}</span>
            </div>
            <div className="board-card">
              <Chessboard
                options={{
                  position: fen,
                  boardOrientation,
                  onPieceDrop: onDrop,
                  onSquareClick,
                  canDragPiece,
                  allowDrawingArrows: true,
                  clearArrowsOnPositionChange: false,
                  squareStyles,
                  showAnimations: true,
                  animationDurationInMs: 180,
                  darkSquareStyle: { backgroundColor: '#6f7f69' },
                  lightSquareStyle: { backgroundColor: '#ece3cf' },
                  boardStyle: {
                    borderRadius: '8px',
                    boxShadow: '0 20px 50px rgba(0, 0, 0, 0.32)',
                    overflow: 'hidden',
                  },
                }}
              />
            </div>
          </div>

          <div className="player-strip bottom">
            <div>
              <span className="player-label">{humanColor === 'white' ? 'You' : 'Engine'}</span>
              <strong>{humanColor === 'white' ? 'White' : 'Black'}</strong>
            </div>
            <CapturedRow pieces={humanColor === 'white' ? captured.black : captured.white} />
          </div>
        </section>

        <aside className="control-stack">
          <section className="status-card">
            <div className="status-heading">
              <div>
                <span>Match State</span>
                <strong>{statusText}</strong>
              </div>
              {isThinking ? <Loader2 className="spin" size={24} /> : <Activity size={24} />}
            </div>
            <div className="metric-grid">
              <Metric icon={<Gauge size={16} />} label="Eval" value={getScoreDisplay()} />
              <Metric icon={<Brain size={16} />} label="Depth" value={currentDepth || '-'} />
              <Metric icon={<Timer size={16} />} label="Clock" value={formatTime(thinkTime)} />
              <Metric icon={<Swords size={16} />} label="Material" value={materialDiff > 0 ? `+${materialDiff}` : materialDiff} />
            </div>
          </section>

          {!gameId ? (
            <section className="panel">
              <div className="panel-header">
                <Sparkles size={18} />
                <h2>New Match</h2>
              </div>

              <Field label="Play as">
                <div className="segmented">
                  <button className={humanColor === 'white' ? 'active' : ''} onClick={() => setHumanColor('white')}>White</button>
                  <button className={humanColor === 'black' ? 'active' : ''} onClick={() => setHumanColor('black')}>Black</button>
                </div>
              </Field>

              <Field label={`Engine skill ${skillLevel}`}>
                <input type="range" min="1" max="20" value={skillLevel} onChange={(e) => setSkillLevel(Number(e.target.value))} />
              </Field>

              <Field label={`Think time ${formatTime(thinkTime)}`}>
                <input type="range" min="100" max="10000" step="100" value={thinkTime} onChange={(e) => setThinkTime(Number(e.target.value))} />
              </Field>

              <Field label="Depth cap">
                <select value={depth} onChange={(e) => setDepth(e.target.value)}>
                  <option value="">Time controlled</option>
                  <option value="1">Depth 1</option>
                  <option value="3">Depth 3</option>
                  <option value="5">Depth 5</option>
                  <option value="8">Depth 8</option>
                  <option value="12">Depth 12</option>
                </select>
              </Field>

              <button className="primary-action" onClick={() => startNewGame(humanColor)} disabled={isStarting}>
                {isStarting ? <Loader2 className="spin" size={18} /> : <Play size={18} />}
                Start engine match
              </button>
            </section>
          ) : (
            <section className="panel match-actions">
              <div className="panel-header">
                <Shield size={18} />
                <h2>Controls</h2>
              </div>
              <div className="action-grid">
                <button onClick={() => setBoardOrientation((value) => (value === 'white' ? 'black' : 'white'))}>
                  <RotateCcw size={17} />
                  Flip
                </button>
                <button onClick={() => startNewGame(humanColor)}>
                  <RefreshCcw size={17} />
                  Restart
                </button>
                <button className="danger" onClick={resignGame}>
                  <Flag size={17} />
                  Resign
                </button>
              </div>
            </section>
          )}

          <section className="panel move-panel">
            <div className="panel-header">
              <History size={18} />
              <h2>Move History</h2>
            </div>
            <div className="move-list">
              {movePairs.length === 0 ? (
                <div className="empty-state">
                  <BadgeHelp size={22} />
                  <span>No moves yet</span>
                </div>
              ) : (
                movePairs.map((pair) => (
                  <React.Fragment key={pair.num}>
                    <span className="move-number">{pair.num}.</span>
                    <span className="move-token">{pair.white || ''}</span>
                    <span className="move-token">{pair.black || ''}</span>
                  </React.Fragment>
                ))
              )}
              <div ref={moveHistoryEndRef} />
            </div>
          </section>
        </aside>
      </main>

      {pendingPromotion && (
        <div className="overlay">
          <div className="modal">
            <h2>Promote pawn</h2>
            <div className="promotion-grid">
              {PROMOTION_PIECES.map((piece) => (
                <button
                  key={piece.value}
                  onClick={() => {
                    submitMove({ ...pendingPromotion, promotion: piece.value });
                    setPendingPromotion(null);
                  }}
                >
                  {piece.label}
                </button>
              ))}
            </div>
            <button className="quiet-action" onClick={() => setPendingPromotion(null)}>Cancel</button>
          </div>
        </div>
      )}

      {showModal && (
        <div className="overlay">
          <div className="modal">
            <Crown size={40} />
            <h2>Game completed</h2>
            <p>
              Result <strong>{gameOverInfo.result}</strong>
              {gameOverInfo.reason ? ` by ${gameOverInfo.reason.replaceAll('_', ' ')}` : ''}
            </p>
            <button className="primary-action" onClick={() => startNewGame(humanColor)}>
              <RefreshCcw size={18} />
              Play again
            </button>
            <button className="quiet-action" onClick={resetToSettings}>Change settings</button>
          </div>
        </div>
      )}
    </div>
  );
}

function Field({ label, children }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
    </label>
  );
}

function Metric({ icon, label, value }) {
  return (
    <div className="metric">
      <span>{icon}{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function CapturedRow({ pieces }) {
  const symbols = { p: 'p', n: 'n', b: 'b', r: 'r', q: 'q' };
  return (
    <div className="captured-row" aria-label="Captured material">
      {pieces.length ? pieces.map((piece, index) => <span key={`${piece}-${index}`}>{symbols[piece]}</span>) : <span className="none">No captures</span>}
    </div>
  );
}
