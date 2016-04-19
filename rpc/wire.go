package rpc

import (
	"bufio"
	"encoding/binary"
	"io"
	"net"
)

type Wire struct {
	writer *bufio.Writer
	reader io.Reader
}

func NewWire(conn net.Conn) *Wire {
	return &Wire{
		writer: bufio.NewWriterSize(conn, writeBufferSize),
		reader: bufio.NewReaderSize(conn, readBufferSize),
	}
}

func (w *Wire) Write(msg *Message) error {
	if err := binary.Write(w.writer, binary.LittleEndian, msg.Seq); err != nil {
		return err
	}
	if err := binary.Write(w.writer, binary.LittleEndian, msg.Type); err != nil {
		return err
	}
	if err := binary.Write(w.writer, binary.LittleEndian, msg.Offset); err != nil {
		return err
	}
	if err := binary.Write(w.writer, binary.LittleEndian, uint32(len(msg.Data))); err != nil {
		return err
	}
	if len(msg.Data) > 0 {
		if _, err := w.writer.Write(msg.Data); err != nil {
			return err
		}
	}
	return w.writer.Flush()
}

func (w *Wire) Read() (*Message, error) {
	var (
		msg    Message
		length uint32
	)

	if err := binary.Read(w.reader, binary.LittleEndian, &msg.Seq); err != nil {
		return nil, err
	}

	if err := binary.Read(w.reader, binary.LittleEndian, &msg.Type); err != nil {
		return nil, err
	}

	if err := binary.Read(w.reader, binary.LittleEndian, &msg.Offset); err != nil {
		return nil, err
	}

	if err := binary.Read(w.reader, binary.LittleEndian, &length); err != nil {
		return nil, err
	}

	if length > 0 {
		msg.Data = make([]byte, length)
		if _, err := io.ReadFull(w.reader, msg.Data); err != nil {
			return nil, err
		}
	}

	return &msg, nil
}