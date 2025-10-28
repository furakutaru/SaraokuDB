import { promises as fs } from 'fs';
import path from 'path';
import { NextApiRequest, NextApiResponse } from 'next';

interface ErrorWithCode extends Error {
  code?: string;
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  // 環境変数から静的ファイルのベースディレクトリを取得
  const baseDir = process.env.STATIC_FILES_DIR || path.join(process.cwd(), '..', 'static-frontend', 'public');
  
  // クエリパラメータから相対パスを取得
  const { path: relativePath } = req.query;
  
  // パスの検証
  if (!relativePath || typeof relativePath !== 'string') {
    return res.status(400).json({ 
      error: 'パスが指定されていません',
      usage: '/api/read-local-file?path=relative/path/from/static/dir',
      baseDir
    });
  }

  try {
    // 絶対パスを構築
    const absolutePath = path.join(baseDir, relativePath);
    
    // パストラバーサル攻撃を防ぐため、ベースディレクトリ内に収まっているか検証
    const normalizedPath = path.normalize(absolutePath);
    const normalizedBaseDir = path.normalize(baseDir);
    
    if (!normalizedPath.startsWith(normalizedBaseDir)) {
      return res.status(403).json({ 
        error: 'アクセスが許可されていないパスです',
        path: relativePath,
        baseDir: normalizedBaseDir,
        normalizedPath
      });
    }

    // ファイルを読み込む
    const fileContent = await fs.readFile(normalizedPath, 'utf-8');
    
    // JSONとしてパースして返す
    try {
      const data = JSON.parse(fileContent);
      return res.status(200).json(data);
    } catch (e) {
      // JSONとしてパースできない場合は生のテキストとして返す
      return res.status(200).send(fileContent);
    }
  } catch (error: unknown) {
    const err = error as ErrorWithCode;
    console.error('ファイルの読み込み中にエラーが発生しました:', {
      error: err,
      message: err.message,
      code: err.code,
      baseDir,
      relativePath,
      stack: process.env.NODE_ENV === 'development' ? err.stack : undefined
    });
    
    // ファイルが存在しない場合
    if (err.code === 'ENOENT') {
      return res.status(404).json({ 
        error: 'ファイルが見つかりません',
        path: relativePath,
        baseDir,
        details: err.message
      });
    }
    
    // その他のエラー
    return res.status(500).json({ 
      error: 'ファイルの読み込みに失敗しました',
      details: err.message,
      path: relativePath,
      baseDir
    });
  }
}
